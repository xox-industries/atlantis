import { StartOptions } from '@/src/commands/start'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const startTerrariaAction = async (options: StartOptions) => {
  const { displayTerrariaInstances: instances } =
    await graphQLClient.ATL_CommandsStartTerraria_DisplayTerrariaInstances()

  if (!instances.some((i) => !i.running)) {
    p.log.warn('No Terraria manifests available to start')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Terraria manifest',
      options: instances.map((instance) => ({
        value: instance.path,
        label: chalk.magentaBright(instance.path === '' ? '.' : instance.path),
        hint: instance.running ? `port ${instance.port}) (already running` : undefined,
        disabled: instance.running,
      })),
    })
  )

  if (!options.skipSteamValidate) {
    const updating = p.taskLog({ title: 'Checking Terraria application', limit: 5 })
    for await (const result of graphQLClient.ATL_CommandsStartTerraria_TerrariaValidateApp(
      {
        path: selected,
      }
    )) {
      const line = result.terrariaValidateApp
      if (line.trim().length > 0) {
        updating.message(line)
      }
    }
    updating.success('Terraria application check complete')
  }

  const starting = p.spinner()
  starting.start(
    `Starting Terraria instance ${chalk.magentaBright(selected === '' ? '.' : selected)}`
  )
  try {
    const { startTerraria: started } =
      await graphQLClient.ATL_CommandsStartTerraria_StartTerraria({
        path: selected,
      })
    starting.stop(
      `Terraria instance ${chalk.magentaBright(
        started.path === '' ? '.' : started.path
      )} started ${chalk.gray(`on port ${started.port}`)}`
    )

    return started.containerName
  } catch (e) {
    starting.cancel()
    throw e
  }
}

const startTerrariaCommand = new AtlantisCommand('terraria')
  .description('Start a Terraria instance')
  .option('--skip-steam-validate', 'Skip Steam validation before starting')
  .action(async (options: StartOptions) => {
    await startTerrariaAction(options)
  })

export default startTerrariaCommand
