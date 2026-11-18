// Python Function App on the Linux Consumption plan, linked to the Static Web App.
// Code runs from a zip in Blob Storage, fetched with the user-assigned identity
// (no SAS, no shared keys). scripts/deploy.sh uploads the zip.
param location string
param name string
param planName string
param identityId string
param identityClientId string
param storageAccountName string
param packageUrl string
param keyVaultUri string
param appInsightsConnectionString string
param transcriptionProvider string
param generationProvider string
param tags object

resource plan 'Microsoft.Web/serverfarms@2024-04-01' = {
  name: planName
  location: location
  tags: tags
  kind: 'functionapp'
  sku: {
    name: 'Y1'
    tier: 'Dynamic'
  }
  properties: {
    reserved: true // Linux
  }
}

resource site 'Microsoft.Web/sites@2024-04-01' = {
  name: name
  location: location
  tags: tags
  kind: 'functionapp,linux'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${identityId}': {}
    }
  }
  properties: {
    serverFarmId: plan.id
    httpsOnly: true
    keyVaultReferenceIdentity: identityId
    siteConfig: {
      linuxFxVersion: 'Python|3.12'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      http20Enabled: true
      appSettings: [
        { name: 'FUNCTIONS_EXTENSION_VERSION', value: '~4' }
        { name: 'FUNCTIONS_WORKER_RUNTIME', value: 'python' }
        // Host + Durable Functions storage via managed identity
        { name: 'AzureWebJobsStorage__accountName', value: storageAccountName }
        { name: 'AzureWebJobsStorage__credential', value: 'managedidentity' }
        { name: 'AzureWebJobsStorage__clientId', value: identityClientId }
        // Code package, fetched with the managed identity
        { name: 'WEBSITE_RUN_FROM_PACKAGE', value: packageUrl }
        { name: 'WEBSITE_RUN_FROM_PACKAGE_BLOB_MI_RESOURCE_ID', value: identityId }
        { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: appInsightsConnectionString }
        // DefaultAzureCredential picks the user-assigned identity from this
        { name: 'AZURE_CLIENT_ID', value: identityClientId }
        // App configuration
        { name: 'PRISM_ENV', value: 'azure' }
        { name: 'PRISM_STORAGE_ACCOUNT_NAME', value: storageAccountName }
        { name: 'PRISM_KEY_VAULT_URI', value: keyVaultUri }
        { name: 'PRISM_TRANSCRIPTION_PROVIDER', value: transcriptionProvider }
        { name: 'PRISM_GENERATION_PROVIDER', value: generationProvider }
      ]
    }
  }
}

// No FTP / SCM basic-auth publishing; deploys go through Blob + managed identity.
resource ftpPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-04-01' = {
  parent: site
  name: 'ftp'
  properties: {
    allow: false
  }
}

resource scmPolicy 'Microsoft.Web/sites/basicPublishingCredentialsPolicies@2024-04-01' = {
  parent: site
  name: 'scm'
  properties: {
    allow: false
  }
}

output id string = site.id
output name string = site.name
output defaultHostname string = site.properties.defaultHostName
