import startMinecraftJavaEditionCommand, {
  startMinecraftJavaEditionAction,
} from '@/src/commands/start/minecraft-java-edition'
import startPalworldCommand, { startPalworldAction } from '@/src/commands/start/palworld'
import { AtlantisCommand } from '@/src/lib/command'
import { code } from '@/src/lib/strings'
import { ensureNotCancelled } from '@/src/lib/prompts'
import * as p from '@clack/prompts'
import { Box, render, Text } from 'ink'

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

  let containerName: string | undefined
  switch (choice) {
    case 'minecraft-java-edition':
      containerName = await startMinecraftJavaEditionAction()
      break

    case 'palworld':
      containerName = await startPalworldAction(options)
      break

    default:
      break
  }

  if (containerName) {
    const { unmount } = render(
      <Box display="flex" flexDirection="column" padding={1}>
        <Text>
          Attach to the console with {code(`docker attach ${containerName}`)}.
        </Text>
        <Text>
          Detach without stopping the server by pressing {code('Ctrl+P')},
          then {code('Ctrl+Q')}.
        </Text>
      </Box>
    )
    unmount()
  }
}

const startCommand = new AtlantisCommand('start')
  .description('Show startable services')
  .option('--skip-steam-validate', 'Skip Steam validation before starting')
  .action(action)
  .addCommand(startPalworldCommand)
  .addCommand(startMinecraftJavaEditionCommand)

export default startCommand
