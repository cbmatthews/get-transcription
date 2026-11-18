// User-assigned managed identity for the Function App. Created before the app so
// every role assignment exists by the time the app first starts.
param location string
param name string
param tags object

resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: name
  location: location
  tags: tags
}

output id string = identity.id
output clientId string = identity.properties.clientId
output principalId string = identity.properties.principalId
