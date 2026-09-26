import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const steamValidateAction = async (...args: unknown[]) => {
  const appId = typeof args[0] === 'string' ? args[0] : undefined
  const targetAppId =
    appId ??
    ensureNotCancelled(await p.text({ message: 'Enter the Steam App ID to validate' }))

  const platform = ensureNotCancelled(
    await p.select({
      message: 'Select a platform',
      options: [
        { value: 'LINUX', label: 'Linux' },
        { value: 'WINDOWS', label: 'Windows' },
      ],
    })
  )

  const anonymous = ensureNotCancelled(
    await p.confirm({
      message: 'Validate anonymously?',
      initialValue: false,
    })
  )

  const validating = p.taskLog({
    title: `Validating Steam app ${chalk.magentaBright(targetAppId)}`,
    limit: 5,
  })
  for await (const result of graphQLClient.ATL_CommandsSteamValidate_ValidateApp({
    appId: targetAppId,
    anonymous,
    platform,
  })) {
    const line = result.steamValidateApp
    if (line.trim().length > 0) {
      validating.message(line)
    }
  }
  validating.success(`Steam app ${chalk.magentaBright(targetAppId)} validation complete`)
}

const steamValidateCommand = new AtlantisCommand('validate')
  .description('Validate a Steam application')
  .argument('<app_id>')
  .action(steamValidateAction)

export default steamValidateCommand
