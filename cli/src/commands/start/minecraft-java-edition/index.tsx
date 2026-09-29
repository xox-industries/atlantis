import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const startMinecraftJavaEditionAction = async () => {
  const { displayMinecraftJavaEditionInstances: instances } =
    await graphQLClient.ATL_CommandsStartMinecraftJavaEdition_DisplayMinecraftJavaEditionInstances()

  if (!instances.some((i) => !i.running)) {
    p.log.warn('No Minecraft Java Edition instances available to start')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a Minecraft Java Edition instance',
      options: instances.map((instance) => ({
        value: instance.path,
        label: chalk.magentaBright(instance.path || 'default'),
        hint: instance.running ? `port ${instance.port} (already running)` : undefined,
        disabled: instance.running,
      })),
    })
  )

  const starting = p.taskLog({
    title: `Starting Minecraft Java Edition instance ${chalk.magentaBright(selected)}`,
    limit: 5,
  })
  for await (const result of graphQLClient.ATL_CommandsStartMinecraftJavaEdition_StartMinecraftJavaEdition(
    { path: selected }
  )) {
    const line = result.startMinecraftJavaEdition
    if (line.trim().length > 0) {
      starting.message(line)
    }
  }

  const { displayMinecraftJavaEditionInstances: updatedInstances } =
    await graphQLClient.ATL_CommandsStartMinecraftJavaEdition_DisplayMinecraftJavaEditionInstances()
  const updated = updatedInstances.find((instance) => instance.path === selected)

  starting.success(
    `Minecraft Java Edition instance ${chalk.magentaBright(selected)} started ${chalk.gray(
      `on port ${updated?.port}`
    )}`
  )

  return updated?.containerName
}

const startMinecraftJavaEditionCommand = new AtlantisCommand('minecraft-java-edition')
  .description('Start a Minecraft Java Edition instance')
  .action(async () => {
    await startMinecraftJavaEditionAction()
  })

export default startMinecraftJavaEditionCommand
