// Storage account: media uploads, extracted audio, job records, the backend code
// package and the Functions/Durable host state. Shared-key access is disabled;
// everything (including the browser upload SAS in M1) uses Entra ID.
param location string
param name string
param functionPrincipalId string
param deployerPrincipalId string
param tags object

var appContainers = [
  'uploads' // raw files from the browser (M1)
  'audio' // extracted / downloaded audio (M1, M2)
  'jobs' // job records: jobs/{ownerId}/{jobId}.json
]
var deploymentContainer = 'deployments'
var packageBlobName = 'backend.zip'

// Built-in role definition IDs
var roles = {
  blobDataOwner: 'b7e6dc6d-f1e8-4753-8033-0f276bb0955b'
  blobDataContributor: 'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
  queueDataContributor: '974c5e8b-45b9-4653-ba55-5f855dd0fb88'
  tableDataContributor: '0a9a7e1f-b9d0-4cc4-a60d-0319b160aaa3'
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: name
  location: location
  tags: tags
  kind: 'StorageV2'
  sku: {
    name: 'Standard_LRS'
  }
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    defaultToOAuthAuthentication: true
    publicNetworkAccess: 'Enabled'
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}

resource containers 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = [
  for c in concat(appContainers, [deploymentContainer]): {
    parent: blobService
    name: c
    properties: {
      publicAccess: 'None'
    }
  }
]

// Function App identity: host storage (blobs, queues, tables for Durable Functions)
// and app data. Blob Data Owner also covers user-delegation SAS for M1 uploads.
var functionRoles = [
  roles.blobDataOwner
  roles.queueDataContributor
  roles.tableDataContributor
]

resource functionRoleAssignments 'Microsoft.Authorization/roleAssignments@2022-04-01' = [
  for roleId in functionRoles: {
    name: guid(storage.id, functionPrincipalId, roleId)
    scope: storage
    properties: {
      principalId: functionPrincipalId
      principalType: 'ServicePrincipal'
      roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roleId)
    }
  }
]

// Deployer: upload the backend package and inspect job records in the portal.
resource deployerBlobAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(deployerPrincipalId)) {
  name: guid(storage.id, deployerPrincipalId, roles.blobDataContributor)
  scope: storage
  properties: {
    principalId: deployerPrincipalId
    principalType: 'User'
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', roles.blobDataContributor)
  }
}

output name string = storage.name
output blobEndpoint string = storage.properties.primaryEndpoints.blob
output deploymentContainer string = deploymentContainer
output packageBlobName string = packageBlobName
output packageUrl string = '${storage.properties.primaryEndpoints.blob}${deploymentContainer}/${packageBlobName}'
