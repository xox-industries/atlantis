import minecraftJavaEditionCommand, {
  minecraftJavaEditionCommandAction,
} from '@/src/commands/create/minecraft-java-edition'
import createPalworldCommand, {
  createPalworldAction,
} from '@/src/commands/create/palworld'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

const action = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a service to create',
      options: [
        { value: 'minecraft-java-edition', label: 'Minecraft (Java Edition)' },
        { value: 'palworld', label: 'Palworld (Windows)' },
      ],
    })
  )

  switch (choice) {
    case 'minecraft-java-edition':
      await minecraftJavaEditionCommandAction()
      break

    case 'palworld':
      await createPalworldAction()
      break

    default:
      break
  }
}

const createCommand = new AtlantisCommand('create')
  .description('Show creatable services')
  .action(action)
  .addCommand(minecraftJavaEditionCommand)
  .addCommand(createPalworldCommand)

export default createCommand
