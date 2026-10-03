import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const stopTModLoaderAction = async () => {
  const { displayTmodloaderInstances: instances } =
    await graphQLClient.ATL_CommandsStopTModLoader_DisplayTModLoaderInstances()

  if (!instances.some((i) => i.running)) {
    p.log.warn('No running TModLoader instances available')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a TModLoader instance',
      options: instances
        .filter((instance) => instance.running)
        .map((instance) => ({
          value: instance.path,
          label: chalk.magentaBright(instance.path === '' ? '.' : instance.path),
        })),
    })
  )

  const stopping = p.taskLog({
    title: `Stopping TModLoader instance ${chalk.magentaBright(
      selected === '' ? '.' : selected
    )}`,
    limit: 5,
  })
  for await (const result of graphQLClient.ATL_CommandsStopTModLoader_StopTModLoader({
    path: selected,
  })) {
    const line = result.stopTmodloader
    if (line.trim().length > 0) {
      stopping.message(line)
    }
  }

  stopping.success(
    `TModLoader instance ${chalk.magentaBright(selected === '' ? '.' : selected)} stopped`
  )
}

const stopTModLoaderCommand = new AtlantisCommand('tmodloader')
  .description('Stop a TModLoader instance')
  .action(stopTModLoaderAction)

export default stopTModLoaderCommand
