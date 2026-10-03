import { AtlantisCommand } from '@/src/lib/command'
import { graphQLClient } from '@/src/stores/graphql'
import * as p from '@clack/prompts'
import chalk from 'chalk'

export const createValheimAction = async () => {
  const creating = p.spinner()
  creating.start('Creating Valheim instance')
  try {
    const { createValheim: created } =
      await graphQLClient.ATL_CommandsCreateValheim_CreateValheim()
    creating.stop(`Valheim instance ${chalk.magentaBright(created.name)} created`)
  } catch (e) {
    creating.cancel()
    throw e
  }
}

const createValheimCommand = new AtlantisCommand('valheim')
  .description('Create a Valheim instance')
  .action(createValheimAction)

export default createValheimCommand
