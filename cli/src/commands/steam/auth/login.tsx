import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'

export const steamAuthLoginAction = async () => {
  const username = ensureNotCancelled(
    await p.text({ message: 'Enter your Steam username' })
  )
  const password = ensureNotCancelled(
    await p.password({ message: 'Enter your Steam password' })
  )
  const needsCode = ensureNotCancelled(
    await p.confirm({ message: 'Do you have a Steam Guard code?' })
  )
  const code = needsCode
    ? ensureNotCancelled(await p.text({ message: 'Enter your Steam Guard code' }))
    : null

  const loggingIn = p.taskLog({ title: 'Logging in to Steam', limit: 5 })
  for await (const result of graphQLClient.ATL_CommandsSteamAuthLogin_SteamLogin({
    username,
    password,
    code,
  })) {
    const line = result.steamLogin
    if (line.trim().length > 0) {
      loggingIn.message(line)
    }
  }
  loggingIn.success('Steam login complete')
}

const steamAuthLoginCommand = new AtlantisCommand('login')
  .description('Log in to Steam')
  .action(steamAuthLoginAction)

export default steamAuthLoginCommand
