import createMinecraftJavaEditionCommand, {
  createMinecraftJavaEditionAction,
} from '@/src/commands/create/minecraft-java-edition/create'
import updateMinecraftJavaEditionCommand, {
  updateMinecraftJavaEditionAction,
} from '@/src/commands/create/minecraft-java-edition/update'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

export { createMinecraftJavaEditionAction, updateMinecraftJavaEditionAction }

export const minecraftJavaEditionCommandAction = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select an action for Minecraft (Java Edition)',
      options: [
        { value: 'create', label: 'Create a new modpack manifest' },
        { value: 'update', label: 'Update an existing modpack manifest' },
      ],
    })
  )

  if (choice === 'create') {
    await createMinecraftJavaEditionAction()
  } else {
    await updateMinecraftJavaEditionAction()
  }
}

const minecraftJavaEditionCommand = new AtlantisCommand('minecraft-java-edition')
  .description('Minecraft (Java Edition) options')
  .action(minecraftJavaEditionCommandAction)
  .addCommand(createMinecraftJavaEditionCommand)
  .addCommand(updateMinecraftJavaEditionCommand)

export default minecraftJavaEditionCommand
