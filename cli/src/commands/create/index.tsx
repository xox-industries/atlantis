import minecraftJavaEditionCommand, {
  minecraftJavaEditionCommandAction,
} from '@/src/commands/create/minecraft-java-edition'
import createPalworldCommand, {
  createPalworldAction,
} from '@/src/commands/create/palworld'
import terrariaCommand, { terrariaCommandAction } from '@/src/commands/create/terraria'
import tmodloaderCommand, {
  tmodloaderCommandAction,
} from '@/src/commands/create/tmodloader'
import createValheimCommand, { createValheimAction } from '@/src/commands/create/valheim'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

const action = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a service to create',
      options: [
        {
          value: 'minecraft-java-edition',
          label: 'Minecraft (Java Edition) (Vanilla | Modded)',
        },
        { value: 'palworld', label: 'Palworld' },
        { value: 'terraria', label: 'Terraria' },
        { value: 'tmodloader', label: 'TModLoader (Modded Terraria)' },
        { value: 'valheim', label: 'Valheim' },
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

    case 'tmodloader':
      await tmodloaderCommandAction()
      break

    case 'valheim':
      await createValheimAction()
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
  .addCommand(tmodloaderCommand)
  .addCommand(createValheimCommand)

export default createCommand
