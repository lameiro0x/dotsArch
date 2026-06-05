# Starship prompt
if status is-interactive
    starship init fish | source
end

# Aliases — bat y lsd
alias cat 'bat'
alias ls 'lsd'
alias ll 'lsd -la'
alias la 'lsd -a'
alias l 'lsd'

# PATH local
fish_add_path ~/.local/bin
