import { AtlantisCommand } from '@/src/lib/command'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const createPalworldAction = async () => {
  const creating = p.spinner()
  creating.start('Creating Palworld instance')
  try {
    const { createPalworld: created } =
      await graphQLClient.ATL_CommandsCreatePalworld_CreatePalworld()
    creating.stop(`Palworld instance ${chalk.magentaBright(created.path)} created`)
  } catch (e) {
    creating.cancel()
    throw e
  }
}

const createPalworldCommand = new AtlantisCommand('palworld')
  .description('Create a Palworld instance')
  .action(createPalworldAction)

export default createPalworldCommand
