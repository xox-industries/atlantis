import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const stopTerrariaAction = async () => {
  const { displayTerrariaInstances: instances } =
    await graphQLClient.ATL_CommandsStopTerraria_DisplayTerrariaInstances()

  if (!instances.some((i) => i.running)) {
    p.log.warn('No running Terraria instances available')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Terraria instance',
      options: instances
        .filter((instance) => instance.running)
        .map((instance) => ({
          value: instance.path,
          label: chalk.magentaBright(instance.path === '' ? '.' : instance.path),
        })),
    })
  )

  const stopping = p.taskLog({
    title: `Stopping Terraria instance ${chalk.magentaBright(
      selected === '' ? '.' : selected
    )}`,
    limit: 5,
  })
  for await (const result of graphQLClient.ATL_CommandsStopTerraria_StopTerraria({
    path: selected,
  })) {
    const line = result.stopTerraria
    if (line.trim().length > 0) {
      stopping.message(line)
    }
  }

  stopping.success(
    `Terraria instance ${chalk.magentaBright(selected === '' ? '.' : selected)} stopped`
  )
}

const stopTerrariaCommand = new AtlantisCommand('terraria')
  .description('Stop a Terraria instance')
  .action(stopTerrariaAction)

export default stopTerrariaCommand
