import { AtlantisCommand } from '@/src/lib/command'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'

export const steamAuthLogoutAction = async () => {
  await graphQLClient.ATL_CommandsSteamAuthLogout_SteamLogout()
  p.log.success('Logged out of Steam')
}

const steamAuthLogoutCommand = new AtlantisCommand('logout')
  .description('Log out of Steam')
  .action(steamAuthLogoutAction)

export default steamAuthLogoutCommand
