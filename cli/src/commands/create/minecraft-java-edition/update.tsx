import { AtlantisCommand } from '@/src/lib/command'
import { ensureNotCancelled } from '@/src/lib/prompts'
import { isPositiveInteger } from '@/src/lib/strings'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'
import { MinecraftModloaderType, MODLOADER_OPTIONS } from './shared'

const validateMinecraftVersion = async (version: string): Promise<boolean> => {
  const { validateMinecraftJavaEditionVersion: valid } =
    await graphQLClient.ATL_CommandsCreateMinecraftJavaEdition_ValidateMinecraftJavaEditionVersion(
      {
        versionType: 'minecraft',
        minecraftVersion: version,
      }
    )
  return valid
}

const validateModloaderVersion = async (
  type: string,
  minecraftVersion: string,
  version: string
): Promise<boolean> => {
  const { validateMinecraftJavaEditionVersion: valid } =
    await graphQLClient.ATL_CommandsCreateMinecraftJavaEdition_ValidateMinecraftJavaEditionVersion(
      {
        versionType: type,
        minecraftVersion: minecraftVersion,
        modloaderVersion: version,
      }
    )
  return valid
}

export const updateMinecraftJavaEditionAction = async () => {
  const { displayMinecraftJavaEdition: manifests } =
    await graphQLClient.ATL_CommandsCreateMinecraftJavaEdition_DisplayMinecraftJavaEdition()

  if (manifests.length === 0) {
    p.log.warn('No Minecraft Java Edition manifests found')
    return
  }

  const selected = ensureNotCancelled(
    await p.select({
      message: 'Select a modpack manifest to update',
      options: manifests.map((manifest) => ({
        value: manifest.path,
        label: manifest.path === '' ? '.' : manifest.path,
      })),
    })
  )

  const manifest = manifests.find((m) => m.path === selected)
  if (manifest === undefined) {
    throw new Error('Selected manifest not found')
  }

  const modloaderType = ensureNotCancelled(
    await p.select<MinecraftModloaderType>({
      message: 'Modloader type',
      options: MODLOADER_OPTIONS,
      initialValue: manifest.modLoader.type as MinecraftModloaderType,
    })
  )

  const minecraftVersion = ensureNotCancelled(
    await p.text({
      message: 'Minecraft version',
      initialValue: manifest.minecraftVersion,
      validate: async (value) => {
        if (value === undefined || value.trim().length === 0) {
          return 'Minecraft version is required'
        }
        if (!(await validateMinecraftVersion(value.trim()))) {
          return `Minecraft version ${value.trim()} not found`
        }
        return undefined
      },
    })
  )

  const { latestMinecraftJavaEditionModloaderVersion: latestModloaderVersion } =
    await graphQLClient.ATL_CommandsCreateMinecraftJavaEdition_LatestMinecraftJavaEditionModloaderVersion(
      {
        modloaderType: modloaderType,
        minecraftVersion: minecraftVersion.trim(),
      }
    )

  const modloaderVersion = ensureNotCancelled(
    await p.text({
      message: 'Modloader version',
      initialValue:
        modloaderType === manifest.modLoader.type &&
        minecraftVersion === manifest.minecraftVersion
          ? manifest.modLoader.version
          : latestModloaderVersion,
      validate: async (value) => {
        if (value === undefined || value.trim().length === 0) {
          return 'Modloader version is required'
        }
        if (
          !(await validateModloaderVersion(
            modloaderType,
            minecraftVersion.trim(),
            value.trim()
          ))
        ) {
          return `${modloaderType} version ${value.trim()} not found for Minecraft ${minecraftVersion.trim()}`
        }
        return undefined
      },
    })
  )

  const ramInput = ensureNotCancelled(
    await p.text({
      message: 'RAM in MB',
      initialValue: manifest.ram.toString(),
      validate: (value) => {
        if (value === undefined || !isPositiveInteger(value)) {
          return 'RAM must be a positive integer'
        }
        if (parseInt(value, 10) < 1000) {
          return 'RAM must be at least 1000 MB'
        }
        return undefined
      },
    })
  )

  const updating = p.spinner()
  updating.start('Updating Minecraft Java Edition manifest')

  try {
    const { updateMinecraftJavaEdition: updated } =
      await graphQLClient.ATL_CommandsCreateMinecraftJavaEdition_UpdateMinecraftJavaEdition(
        {
          path: selected,
          minecraftVersion: minecraftVersion.trim(),
          modloaderType: modloaderType,
          modloaderVersion: modloaderVersion.trim(),
          ram: parseInt(ramInput, 10),
        }
      )

    updating.stop(
      `Updated manifest at ${chalk.magentaBright(
        updated.path === ''
          ? 'minecraft-java-edition/atlantis.json'
          : `${updated.path}/atlantis.json`
      )}`
    )
  } catch (e) {
    updating.cancel()
    throw e
  }
}

const updateMinecraftJavaEditionCommand = new AtlantisCommand('update')
  .description('Update an existing Minecraft Java Edition modpack manifest')
  .action(updateMinecraftJavaEditionAction)

export default updateMinecraftJavaEditionCommand
