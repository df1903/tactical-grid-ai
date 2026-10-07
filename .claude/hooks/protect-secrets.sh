#!/usr/bin/env bash
# PreToolUse: bloquea acceso a archivos sensibles (.env*, claves). Permite .env.example.
# Usa jq si está disponible; si no, analiza el JSON crudo (menos preciso, pero bloquea igual).
input=$(cat)
if command -v jq >/dev/null 2>&1; then
  target=$(printf '%s' "$input" | jq -r '.tool_input.file_path // .tool_input.command // ""')
else
  target="$input"
fi
# Quita .env.example antes de evaluar, para que no sirva de coartada junto a un .env real.
check=$(printf '%s' "$target" | sed -E 's/\.env\.example//g')
if printf '%s' "$check" | grep -Eq '(^|[/[:space:]"'\''=])\.env(\.[A-Za-z0-9_-]+)?($|[^A-Za-z0-9_.-])|id_rsa|id_ed25519|\.pem($|[^A-Za-z0-9_-])'; then
  echo "Bloqueado: acceso a archivo sensible." >&2
  exit 2
fi
exit 0
