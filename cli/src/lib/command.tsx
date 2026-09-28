import chalk from 'chalk'
import { Command, Help } from 'commander'
import { Box, render, Text } from 'ink'

const bold = (text: string): string => chalk.bold(text)
const cyan = (text: string): string => chalk.cyanBright(text)
const gray = (text: string): string => chalk.grey(text)
const magenta = (text: string): string => chalk.magentaBright(text)

class CustomHelp extends Help {
  override commandUsage(cmd: Command): string {
    const usage = super.commandUsage(cmd)
    return usage
      .replace('[options]', cyan('[...flags]'))
      .replace('[command]', '<command>')
  }

  override formatHelp(cmd: Command, helper: Help): string {
    const description = helper.commandDescription(cmd)
    const usage = helper.commandUsage(cmd)
    const commands = helper.visibleCommands(cmd)
    const options = helper.visibleOptions(cmd)

    const commandTermWidth = Math.max(
      ...commands.map((c) => {
        const args = c.args.join(' ')
        return `${c.name()} ${args}`.trim().length
      })
    )

    const commandLines = commands.map((c) => {
      const name = c.name()
      const args = c.args
      const coloredTerm = [magenta(name), ...args].join(' ').trim()
      const rawTerm = [name, ...args].join(' ').trim()
      const paddedTerm = coloredTerm.padEnd(
        commandTermWidth + (coloredTerm.length - rawTerm.length)
      )
      const desc = helper.subcommandDescription(c)
      return `  ${paddedTerm}  ${gray(desc)}`
    })

    const optionTermWidth = Math.max(...options.map((o) => helper.optionTerm(o).length))

    const optionLines = options.map((o) => {
      const term = helper.optionTerm(o)
      const coloredTerm = cyan(term)
      const paddedTerm = coloredTerm.padEnd(
        optionTermWidth + (coloredTerm.length - term.length)
      )
      const desc = helper.optionDescription(o)
      return `  ${paddedTerm}  ${gray(desc)}`
    })

    const sections: string[] = []

    if (description) {
      sections.push(description)
      sections.push('')
    }

    sections.push(`${bold('Usage:')} ${usage}`)
    sections.push('')

    if (commandLines.length > 0) {
      sections.push(bold('Commands:'))
      sections.push(...commandLines)
    }

    if (optionLines.length > 0) {
      sections.push(bold('Flags:'))
      sections.push(...optionLines)
      sections.push('')
    }

    return sections.join('\n') + '\n'
  }
}

export class AtlantisCommand extends Command {
  constructor(name?: string) {
    super(name)
    this.helpCommand(false)
  }

  override createCommand(name?: string): AtlantisCommand {
    return new AtlantisCommand(name)
  }

  override createHelp(): CustomHelp {
    return new CustomHelp()
  }

  override action<TArgs extends unknown[]>(
    fn: (...args: TArgs) => void | Promise<void>
  ): this {
    return super.action(async (...args: TArgs) => {
      try {
        await fn(...args)
      } catch (e) {
        const message = e instanceof Error ? e.message : 'An unknown error occurred'
        render(
          <Box padding={1}>
            <Text color="red">{message}</Text>
          </Box>
        )
        process.exitCode = 1
      }
    })
  }
}
