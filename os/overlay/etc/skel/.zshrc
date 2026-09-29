# ~/.zshrc — AIsktagOS

# История
HISTFILE=~/.zsh_history
HISTSIZE=50000
SAVEHIST=50000
setopt HIST_IGNORE_DUPS HIST_IGNORE_SPACE SHARE_HISTORY EXTENDED_HISTORY
setopt AUTO_CD INTERACTIVE_COMMENTS NO_BEEP

# Автодополнение с меню и без учёта регистра
autoload -Uz compinit && compinit -d ~/.cache/zcompdump
zstyle ':completion:*' menu select
zstyle ':completion:*' matcher-list 'm:{a-zA-Z}={A-Za-z}'
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

bindkey -e
bindkey '^[[1;5C' forward-word
bindkey '^[[1;5D' backward-word
bindkey '^[[H' beginning-of-line
bindkey '^[[F' end-of-line
bindkey '^[[3~' delete-char

# PATH для пользовательских инструментов (pipx, cargo, go, npm -g)
typeset -U path
path=(~/.local/bin ~/.cargo/bin ~/go/bin ~/.npm-global/bin $path)
export EDITOR=nvim VISUAL=nvim

# Современные замены стандартных утилит
if command -v eza >/dev/null; then
  alias ls='eza --group-directories-first'
  alias ll='eza -lh --git --group-directories-first'
  alias la='eza -lha --git --group-directories-first'
  alias tree='eza --tree'
fi
command -v batcat >/dev/null && alias cat='batcat --paging=never' && alias bat='batcat'
command -v fdfind >/dev/null && alias fd='fdfind'
alias g='git'
alias gs='git status -sb'
alias gl='git log --oneline --graph --decorate -20'
alias lg='lazygit'
alias dc='docker compose'
alias update='sudo apt update && sudo apt full-upgrade && flatpak update -y'

# Плагины и интеграции
[ -f /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh ] && source /usr/share/zsh-autosuggestions/zsh-autosuggestions.zsh
[ -f /usr/share/doc/fzf/examples/key-bindings.zsh ] && source /usr/share/doc/fzf/examples/key-bindings.zsh
command -v zoxide   >/dev/null && eval "$(zoxide init zsh)"
command -v direnv   >/dev/null && eval "$(direnv hook zsh)"
command -v starship >/dev/null && eval "$(starship init zsh)"
# Подсветка синтаксиса должна подключаться последней
[ -f /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh ] && source /usr/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh
