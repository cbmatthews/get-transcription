// Static Web App (Standard) hosting the React frontend. Standard is required to
// link a separate Function App as the /api backend. Linking also configures the
// Function App's authentication so it only accepts traffic from this site.
//
// Sign-in: the built-in Microsoft (aad) provider. Every route requires the custom
// 'owner' role (see frontend/public/staticwebapp.config.json), which is granted
// only through an invitation: scripts/invite-owner.sh.
param location string
param name string
param functionAppId string
param functionAppLocation string
param tags object

resource site 'Microsoft.Web/staticSites@2024-04-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
  properties: {
    stagingEnvironmentPolicy: 'Disabled'
    allowConfigFileUpdates: true
  }
}

resource backend 'Microsoft.Web/staticSites/linkedBackends@2024-04-01' = {
  parent: site
  name: 'backend'
  properties: {
    backendResourceId: functionAppId
    region: functionAppLocation
  }
}

output name string = site.name
output defaultHostname string = site.properties.defaultHostname
