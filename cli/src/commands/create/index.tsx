import minecraftJavaEditionCommand, {
  minecraftJavaEditionCommandAction,
} from '@/src/commands/create/minecraft-java-edition'
import createPalworldCommand, {
  createPalworldAction,
} from '@/src/commands/create/palworld'
import terrariaCommand, { terrariaCommandAction } from '@/src/commands/create/terraria'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

const action = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a service to create',
      options: [
        { value: 'minecraft-java-edition', label: 'Minecraft (Java Edition)' },
        { value: 'palworld', label: 'Palworld' },
        { value: 'terraria', label: 'Terraria' },
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

    case 'terraria':
      await terrariaCommandAction()
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
  .addCommand(terrariaCommand)

export default createCommand
