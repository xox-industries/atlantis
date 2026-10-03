import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const stopValheimAction = async () => {
  const { displayValheim: instances } =
    await graphQLClient.ATL_CommandsStopValheim_DisplayValheim()

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
          value: instance.name,
          label: chalk.magentaBright(instance.name),
        })),
    })
  )

  const stopping = p.spinner()
  stopping.start(`Stopping Valheim instance ${chalk.magentaBright(selected)}`)
  try {
    const { stopValheim: stopped } =
      await graphQLClient.ATL_CommandsStopValheim_StopValheim({
        instance: selected,
      })
    stopping.stop(`Valheim instance ${chalk.magentaBright(stopped.name)} stopped`)
  } catch (e) {
    stopping.cancel()
    throw e
  }
}

const stopValheimCommand = new AtlantisCommand('valheim')
  .description('Stop a Valheim instance')
  .action(stopValheimAction)

export default stopValheimCommand
