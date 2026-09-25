import { AtlantisCommand } from '@/src/lib/command'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const createPalworldAction = async () => {
  const { createPalworld: created } =
    await graphQLClient.ATL_CommandsCreatePalworld_CreatePalworld()

  p.log.success(`Palworld instance ${chalk.magentaBright(created.name)} created`)
}

const createPalworldCommand = new AtlantisCommand('palworld')
  .description('Create a Palworld instance')
  .action(createPalworldAction)

export default createPalworldCommand
