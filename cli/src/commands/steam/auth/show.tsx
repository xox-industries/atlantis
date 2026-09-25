import { AtlantisCommand } from '@/src/lib/command'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'

export const steamAuthShowAction = async () => {
  const { displaySteam: account } =
    await graphQLClient.ATL_CommandsSteamAuthShow_DisplaySteam()

  if (account.username) {
    p.log.success(`Logged in as ${account.username}`)
  } else {
    p.log.warn('No Steam account is currently logged in')
  }
}

const steamAuthShowCommand = new AtlantisCommand('show')
  .description('Show the current Steam account')
  .action(steamAuthShowAction)

export default steamAuthShowCommand
