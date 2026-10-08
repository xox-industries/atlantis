import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const stopValheimAction = async () => {
  const { displayValheimInstances: instances } =
    await graphQLClient.ATL_CommandsStopValheim_DisplayValheimInstances()

  if (!instances.some((i) => i.running)) {
    p.log.warn('No running Valheim instances available')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Valheim instance',
      options: instances
        .filter((instance) => instance.running)
        .map((instance) => ({
          value: instance.path,
          label: chalk.magentaBright(instance.path === '' ? '.' : instance.path),
        })),
    })
  )

  const stopping = p.spinner()
  stopping.start(`Stopping Valheim instance ${chalk.magentaBright(selected)}`)
  try {
    const { stopValheim: stopped } =
      await graphQLClient.ATL_CommandsStopValheim_StopValheim({
        path: selected,
      })
    stopping.stop(
      `Valheim instance ${chalk.magentaBright(stopped.path === '' ? '.' : stopped.path)} stopped`
    )
  } catch (e) {
    stopping.cancel()
    throw e
  }
}

const stopValheimCommand = new AtlantisCommand('valheim')
  .description('Stop a Valheim instance')
  .action(stopValheimAction)

export default stopValheimCommand
