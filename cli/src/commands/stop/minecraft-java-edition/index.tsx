import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const stopMinecraftJavaEditionAction = async () => {
  const { displayMinecraftJavaEditionInstances: instances } =
    await graphQLClient.ATL_CommandsStopMinecraftJavaEdition_DisplayMinecraftJavaEditionInstances()

  if (!instances.some((instance) => instance.running)) {
    p.log.warn('No running Minecraft Java Edition instances available')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Minecraft Java Edition instance',
      options: instances
        .filter((instance) => instance.running)
        .map((instance) => ({
          value: instance.path,
          label: chalk.magentaBright(instance.path || 'default'),
        })),
    })
  )

  const stopping = p.taskLog({
    title: `Stopping Minecraft Java Edition instance ${chalk.magentaBright(
      selected || 'default'
    )}`,
    limit: 5,
  })
  for await (const result of graphQLClient.ATL_CommandsStopMinecraftJavaEdition_StopMinecraftJavaEdition(
    { path: selected }
  )) {
    const line = result.stopMinecraftJavaEdition
    if (line.trim().length > 0) {
      stopping.message(line)
    }
  }

  stopping.success(
    `Minecraft Java Edition instance ${chalk.magentaBright(selected || 'default')} stopped`
  )
}

const stopMinecraftJavaEditionCommand = new AtlantisCommand('minecraft-java-edition')
  .description('Stop a Minecraft Java Edition instance')
  .action(stopMinecraftJavaEditionAction)

export default stopMinecraftJavaEditionCommand
