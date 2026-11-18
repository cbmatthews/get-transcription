// Prism by Kaleidoscope — V1 infrastructure (resource-group scope).
//
// Deploy with scripts/deploy.sh, or directly:
//   az deployment group create -g rg-prism -f infra/main.bicep -p infra/main.bicepparam

targetScope = 'resourceGroup'

@description('Short name used in every resource name.')
@minLength(3)
@maxLength(10)
param appName string = 'prism'

@description('Region for Storage, Key Vault, monitoring and the Function App.')
param location string = resourceGroup().location

@description('Region for the Static Web App (limited set: westus2, centralus, eastus2, westeurope, eastasia).')
@allowed([
  'westus2'
  'centralus'
  'eastus2'
  'westeurope'
  'eastasia'
])
param staticWebAppLocation string = 'eastus2'

@description('Object ID of the person running the deployment. Gets data-plane access to Storage and Key Vault so the deploy script can upload the backend package and you can manage secrets. Leave empty to skip.')
param deployerPrincipalId string = ''

@description('Provider used for transcription. Swapped by config only.')
param transcriptionProvider string = 'fake'

@description('Provider used for summary / action plan generation. Swapped by config only.')
param generationProvider string = 'fake'

param tags object = {
  app: 'prism-by-kaleidoscope'
  env: 'v1'
}

var suffix = uniqueString(resourceGroup().id)

module monitoring 'modules/monitoring.bicep' = {
  name: 'monitoring'
  params: {
    location: location
    logAnalyticsName: 'log-${appName}-${suffix}'
    appInsightsName: 'appi-${appName}-${suffix}'
    tags: tags
  }
}

module identity 'modules/identity.bicep' = {
  name: 'identity'
  params: {
    location: location
    name: 'id-${appName}-${suffix}'
    tags: tags
  }
}

module storage 'modules/storage.bicep' = {
  name: 'storage'
  params: {
    location: location
    name: take('st${appName}${suffix}', 24)
    functionPrincipalId: identity.outputs.principalId
    deployerPrincipalId: deployerPrincipalId
    tags: tags
  }
}

module keyVault 'modules/keyvault.bicep' = {
  name: 'keyvault'
  params: {
    location: location
    name: take('kv-${appName}-${suffix}', 24)
    functionPrincipalId: identity.outputs.principalId
    deployerPrincipalId: deployerPrincipalId
    tags: tags
  }
}

module functionApp 'modules/functionapp.bicep' = {
  name: 'functionapp'
  params: {
    location: location
    name: 'func-${appName}-${suffix}'
    planName: 'plan-${appName}-${suffix}'
    identityId: identity.outputs.id
    identityClientId: identity.outputs.clientId
    storageAccountName: storage.outputs.name
    packageUrl: storage.outputs.packageUrl
    keyVaultUri: keyVault.outputs.uri
    appInsightsConnectionString: monitoring.outputs.appInsightsConnectionString
    transcriptionProvider: transcriptionProvider
    generationProvider: generationProvider
    tags: tags
  }
}

module staticWebApp 'modules/staticwebapp.bicep' = {
  name: 'staticwebapp'
  params: {
    location: staticWebAppLocation
    name: 'swa-${appName}-${suffix}'
    functionAppId: functionApp.outputs.id
    functionAppLocation: location
    tags: tags
  }
}

output resourceGroupName string = resourceGroup().name
output staticWebAppName string = staticWebApp.outputs.name
output staticWebAppHostname string = staticWebApp.outputs.defaultHostname
output functionAppName string = functionApp.outputs.name
output functionAppId string = functionApp.outputs.id
output functionAppHostname string = functionApp.outputs.defaultHostname
output storageAccountName string = storage.outputs.name
output deploymentContainer string = storage.outputs.deploymentContainer
output packageBlobName string = storage.outputs.packageBlobName
output keyVaultName string = keyVault.outputs.name
