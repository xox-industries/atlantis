import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const stopPalworldAction = async () => {
  const { displayPalworldInstances: instances } =
    await graphQLClient.ATL_CommandsStopPalworld_DisplayPalworldInstances()

  if (!instances.some((i) => i.running)) {
    p.log.warn('No running Palworld instances available')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Palworld instance',
      options: instances
        .filter((instance) => instance.running)
        .map((instance) => ({
          value: instance.path,
          label: chalk.magentaBright(instance.path === '' ? '.' : instance.path),
        })),
    })
  )

  const stopping = p.spinner()
  stopping.start(`Stopping Palworld instance ${chalk.magentaBright(selected)}`)
  try {
    const { stopPalworld: stopped } =
      await graphQLClient.ATL_CommandsStopPalworld_StopPalworld({
        path: selected,
      })
    stopping.stop(
      `Palworld instance ${chalk.magentaBright(stopped.path === '' ? '.' : stopped.path)} stopped`
    )
  } catch (e) {
    stopping.cancel()
    throw e
  }
}

const stopPalworldCommand = new AtlantisCommand('palworld')
  .description('Stop a Palworld instance')
  .action(stopPalworldAction)

export default stopPalworldCommand
