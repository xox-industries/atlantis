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

export const createMinecraftJavaEditionAction = async () => {
  const { latestMinecraftJavaEditionMinecraftVersion: latestMinecraftVersion } =
    await graphQLClient.ATL_CommandsCreateMinecraftJavaEdition_LatestMinecraftJavaEditionMinecraftVersion()

  const minecraftVersion = ensureNotCancelled(
    await p.text({
      message: 'Minecraft version',
      initialValue: latestMinecraftVersion,
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

  const modloaderType = ensureNotCancelled(
    await p.select<MinecraftModloaderType>({
      message: 'Modloader type',
      options: MODLOADER_OPTIONS,
      initialValue: 'neoforge',
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
      initialValue: latestModloaderVersion,
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
      initialValue: '8192',
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

  const creating = p.spinner()
  creating.start('Creating Minecraft Java Edition manifest')

  try {
    const { createMinecraftJavaEdition: created } =
      await graphQLClient.ATL_CommandsCreateMinecraftJavaEdition_CreateMinecraftJavaEdition(
        {
          minecraftVersion: minecraftVersion.trim(),
          modloaderType: modloaderType,
          modloaderVersion: modloaderVersion.trim(),
          ram: parseInt(ramInput, 10),
        }
      )

    creating.stop(
      `Created manifest at ${chalk.magentaBright(
        `minecraft-java-edition/${created.path}/atlantis.json`
      )}`
    )
  } catch (e) {
    creating.cancel()
    throw e
  }
}

const createMinecraftJavaEditionCommand = new AtlantisCommand('create')
  .description('Create a Minecraft Java Edition modpack manifest')
  .action(createMinecraftJavaEditionAction)

export default createMinecraftJavaEditionCommand
