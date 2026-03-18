# ACE Ω — GIT PROTOCOLO OFICIAL

Este documento define o fluxo obrigatório de trabalho com o Codex.

## REGRA ABSOLUTA

1. Trabalhar exclusivamente na branch `main`
2. Nunca criar branch `work`, `patch`, `test` ou similares
3. Nunca abrir Pull Request
4. Sempre commit direto na `main`
5. Sempre push para `origin main`

## PROTOCOLO OBRIGATÓRIO ANTES DE QUALQUER ALTERAÇÃO

```
 git remote remove origin || true
 git remote add origin https://github.com/alysonloureiro2011-star/Alessob.git
 git fetch origin
 git checkout main || git checkout -b main origin/main
 git branch --show-current
 git rev-parse --short HEAD
 git status --short --branch
```

Se não estiver em `main`, parar e corrigir.

## APÓS ALTERAÇÃO

```
 git add .
 git commit -m "mensagem clara e objetiva"
 git push origin main
```

## VALIDAÇÃO FINAL OBRIGATÓRIA

Mostrar sempre:

- branch final
- hash final
- resultado de git status
- confirmação de push

---

Este protocolo elimina divergência, branch paralela e perda de tempo.

ACE Ω opera com disciplina de guerra.
