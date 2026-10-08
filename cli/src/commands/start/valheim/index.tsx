import { StartOptions } from '@/src/commands/start'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const startValheimAction = async (options: StartOptions) => {
  const { displayValheimInstances: instances } =
    await graphQLClient.ATL_CommandsStartValheim_DisplayValheimInstances()

  if (!instances.some((i) => !i.running)) {
    p.log.warn('No Valheim instances available to start')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Valheim instance',
      options: instances.map((instance) => ({
        value: instance.path,
        label: chalk.magentaBright(instance.path === '' ? '.' : instance.path),
        hint: instance.running ? `port ${instance.port}) (already running` : undefined,
        disabled: instance.running,
      })),
    })
  )

  if (!options.skipSteamValidate) {
    const updating = p.taskLog({ title: 'Checking Valheim application', limit: 5 })
    for await (const result of graphQLClient.ATL_CommandsStartValheim_ValheimValidateApp({
      path: selected,
    })) {
      const line = result.valheimValidateApp
      if (line.trim().length > 0) {
        updating.message(line)
      }
    }
    updating.success('Valheim application check complete')
  }

  const starting = p.spinner()
  starting.start(`Starting Valheim instance ${chalk.magentaBright(selected)}`)
  try {
    const { startValheim: started } =
      await graphQLClient.ATL_CommandsStartValheim_StartValheim({
        path: selected,
      })
    starting.stop(
      `Valheim instance ${chalk.magentaBright(
        started.path === '' ? '.' : started.path
      )} started ${chalk.gray(`on port ${started.port}`)}`
    )

    return started.containerName
  } catch (e) {
    starting.cancel()
    throw e
  }
}

const startValheimCommand = new AtlantisCommand('valheim')
  .description('Start a Valheim instance')
  .option('--skip-steam-validate', 'Skip Steam validation before starting')
  .action(async (options: StartOptions) => {
    await startValheimAction(options)
  })

export default startValheimCommand
