import stopMinecraftJavaEditionCommand, {
  stopMinecraftJavaEditionAction,
} from '@/src/commands/stop/minecraft-java-edition'
import stopPalworldCommand, { stopPalworldAction } from '@/src/commands/stop/palworld'
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

    default:
      break
  }
}

const stopCommand = new AtlantisCommand('stop')
  .description('Show stoppable services')
  .action(action)
  .addCommand(stopMinecraftJavaEditionCommand)
  .addCommand(stopPalworldCommand)

export default stopCommand
