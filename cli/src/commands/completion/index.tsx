import { AtlantisCommand } from '@/src/lib/command'
import { Command, Option } from 'commander'

const isValidShell = (value: string): value is 'bash' | 'zsh' =>
  value === 'bash' || value === 'zsh'

const extractFlags = (cmd: Command): string[] =>
  Array.from(
    new Set(
      cmd.options
        .flatMap((opt: Option) => [opt.long, opt.short])
        .filter((flag): flag is string => typeof flag === 'string' && flag.length > 0)
    )
  )

const findDeepestCommand = (root: Command, words: string[]): Command => {
  let current = root
  for (const word of words) {
    if (word.startsWith('-')) {
      continue
    }
    const next = current.commands.find((cmd) => cmd.name() === word)
    if (next === undefined) {
      break
    }
    current = next
  }
  return current
}

const getCandidates = (shell: string, words: string[], root: Command): string => {
  const cmd = findDeepestCommand(root, words)
  const commands = cmd.commands.map((c) => c.name())
  const flags = extractFlags(cmd)
  const candidates = [...commands, ...flags]

  if (shell === 'zsh') {
    return candidates.length > 0 ? `${candidates.join('\n')}\n` : ''
  }

  return candidates.join(' ')
}

const bashInstallScript = (binaryName: string): string => `_${binaryName}() {
  local cur="\${COMP_WORDS[COMP_CWORD]}"
  local words=("\${COMP_WORDS[@]:1:$COMP_CWORD-1}")
  local candidates
  candidates="$(${binaryName} completion --candidates bash "\${words[@]}" 2>/dev/null)"
  COMPREPLY=( $(compgen -W "$candidates" -- "$cur") )
}
complete -F _${binaryName} ${binaryName}
`

const zshInstallScript = (binaryName: string): string => `_${binaryName}() {
  local -a candidates
  local words=("\${words[@]:1}")
  candidates=(\${(f)"$(${binaryName} completion --candidates zsh "\${words[@]}" 2>/dev/null)"})
  _describe '${binaryName} commands' candidates
}
compdef _${binaryName} ${binaryName}
`

const generateScript = (shell: string, root: Command): string => {
  const binaryName = root.name()

  switch (shell) {
    case 'bash':
      return bashInstallScript(binaryName)
    case 'zsh':
      return zshInstallScript(binaryName)
    default:
      throw new Error(`Unsupported shell: ${shell}`)
  }
}

type CompletionOptions = {
  candidates?: boolean
}

const action = async (shell: string, _options: CompletionOptions, command: Command) => {
  if (!isValidShell(shell)) {
    throw new Error(`Unsupported shell "${shell}". Supported shells: bash, zsh`)
  }

  const root = command.parent
  if (root === null || root === undefined) {
    throw new Error('Completion command is not attached to a root command')
  }

  if (_options.candidates) {
    const words = command.args.slice(1)
    const candidates = getCandidates(shell, words, root)
    process.stdout.write(candidates)
    return
  }

  process.stdout.write(generateScript(shell, root))
}

const completionCommand = new AtlantisCommand('completion')
  .description('Generate shell completion script')
  .argument('<shell>', 'Shell to generate completion for (bash|zsh)')
  .option('--candidates', 'Output completion candidates (internal use)')
  .allowExcessArguments(true)
  .action(action)

export default completionCommand
