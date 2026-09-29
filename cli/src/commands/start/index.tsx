import startMinecraftJavaEditionCommand, {
  startMinecraftJavaEditionAction,
} from '@/src/commands/start/minecraft-java-edition'
import startPalworldCommand, { startPalworldAction } from '@/src/commands/start/palworld'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'

export type StartOptions = {
  skipSteamValidate?: boolean
}

const action = async (options: StartOptions) => {
  const choice = ensureNotCancelled(
    await p.select({
      message: 'Select a service to start',
      options: [
        { value: 'minecraft-java-edition', label: 'Minecraft (Java Edition)' },
        { value: 'palworld', label: 'Palworld (Windows)' },
      ],
    })
  )

  switch (choice) {
    case 'minecraft-java-edition':
      await startMinecraftJavaEditionAction()
      break

    case 'palworld':
      await startPalworldAction(options)
      break

    default:
      break
  }
}

const startCommand = new AtlantisCommand('start')
  .description('Show startable services')
  .option('--skip-steam-validate', 'Skip Steam validation before starting')
  .action(action)
  .addCommand(startPalworldCommand)
  .addCommand(startMinecraftJavaEditionCommand)

export default startCommand
