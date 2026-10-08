import { printAttachTips, StartOptions } from '@/src/commands/start'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const startTModLoaderAction = async (options: StartOptions) => {
  const { displayTmodloaderInstances: instances } =
    await graphQLClient.ATL_CommandsStartTModLoader_DisplayTModLoaderInstances()

  if (!instances.some((i) => !i.running)) {
    p.log.warn('No TModLoader manifests available to start')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a TModLoader manifest',
      options: instances.map((instance) => ({
        value: instance.path,
        label: chalk.magentaBright(instance.path === '' ? '.' : instance.path),
        hint: instance.running ? `port ${instance.port}) (already running` : undefined,
        disabled: instance.running,
      })),
    })
  )

  if (!options.skipSteamValidate) {
    const updating = p.taskLog({ title: 'Checking TModLoader application', limit: 5 })
    for await (const result of graphQLClient.ATL_CommandsStartTModLoader_TModLoaderValidateApp(
      {
        path: selected,
      }
    )) {
      const line = result.tmodloaderValidateApp
      if (line.trim().length > 0) {
        updating.message(line)
      }
    }
    updating.success('TModLoader application check complete')
  }

  const starting = p.spinner()
  starting.start(
    `Starting TModLoader instance ${chalk.magentaBright(selected === '' ? '.' : selected)}`
  )
  try {
    const { startTmodloader: started } =
      await graphQLClient.ATL_CommandsStartTModLoader_StartTModLoader({
        path: selected,
      })
    starting.stop(
      `TModLoader instance ${chalk.magentaBright(
        started.path === '' ? '.' : started.path
      )} started ${chalk.gray(`on port ${started.port}`)}`
    )

    printAttachTips(started.containerName)
  } catch (e) {
    starting.cancel()
    throw e
  }
}

const startTModLoaderCommand = new AtlantisCommand('tmodloader')
  .description('Start a TModLoader instance')
  .option('--skip-steam-validate', 'Skip Steam validation before starting')
  .action(startTModLoaderAction)

export default startTModLoaderCommand
