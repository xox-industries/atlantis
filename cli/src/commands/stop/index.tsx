import stopMinecraftJavaEditionCommand, {
  stopMinecraftJavaEditionAction,
} from '@/src/commands/stop/minecraft-java-edition'
import stopPalworldCommand, { stopPalworldAction } from '@/src/commands/stop/palworld'
import stopTerrariaCommand, { stopTerrariaAction } from '@/src/commands/stop/terraria'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

const action = async () => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a service to stop',
      options: [
        { value: 'minecraft-java-edition', label: 'Minecraft (Java Edition)' },
        { value: 'palworld', label: 'Palworld' },
        { value: 'terraria', label: 'Terraria' },
      ],
    })
  )

  switch (choice) {
    case 'minecraft-java-edition':
      await stopMinecraftJavaEditionAction()
      break

    case 'palworld':
      await stopPalworldAction()
      break

    case 'terraria':
      await stopTerrariaAction()
      break

    default:
      break
  }
}

const stopCommand = new AtlantisCommand('stop')
  .description('Show stoppable services')
  .action(action)
  .addCommand(stopMinecraftJavaEditionCommand)
  .addCommand(stopPalworldCommand)
  .addCommand(stopTerrariaCommand)

export default stopCommand
