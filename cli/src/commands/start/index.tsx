import startMinecraftJavaEditionCommand, {
  startMinecraftJavaEditionAction,
} from '@/src/commands/start/minecraft-java-edition'
import startPalworldCommand, { startPalworldAction } from '@/src/commands/start/palworld'
import startTerrariaCommand, { startTerrariaAction } from '@/src/commands/start/terraria'
import startTModLoaderCommand, {
  startTModLoaderAction,
} from '@/src/commands/start/tmodloader'
import startValheimCommand, { startValheimAction } from '@/src/commands/start/valheim'
import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { code } from '@/src/lib/strings'
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

  let containerName: string | undefined
  switch (choice) {
    case 'minecraft-java-edition':
      containerName = await startMinecraftJavaEditionAction()
      break

    case 'palworld':
      containerName = await startPalworldAction(options)
      break

    case 'terraria':
      containerName = await startTerrariaAction(options)
      break

    case 'tmodloader':
      containerName = await startTModLoaderAction(options)
      break

    case 'valheim':
      containerName = await startValheimAction(options)
      break

    default:
      break
  }

  if (containerName) {
    const { unmount } = render(
      <Box display="flex" flexDirection="column" padding={1}>
        <Text>Attach to the console with {code(`docker attach ${containerName}`)}.</Text>
        <Text>
          Detach without stopping the server by pressing {code('Ctrl+P')}, then{' '}
          {code('Ctrl+Q')}.
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
  .addCommand(startTerrariaCommand)
  .addCommand(startTModLoaderCommand)
  .addCommand(startValheimCommand)

export default startCommand
