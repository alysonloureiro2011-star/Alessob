# ACE Ω — TEMPLATE OFICIAL DE TAREFA PARA CODEX

Este arquivo elimina atrito operacional.
Copiar e colar SEMPRE no início de qualquer tarefa no Codex.

---

## BLOCO 1 — PROTOCOLO GIT OBRIGATÓRIO

Trabalhe exclusivamente na branch `main`.

Antes de qualquer alteração execute exatamente:

```
 git remote remove origin || true
 git remote add origin https://github.com/alysonloureiro2011-star/Alessob.git
 git fetch origin
 git checkout main || git checkout -b main origin/main
 git branch --show-current
 git rev-parse --short HEAD
 git status --short --branch
```

Se não estiver na `main`, pare e corrija.

Nunca criar:
- branch work
- branch patch
- branch test
- pull request

Após alterações:

```
 git add .
 git commit -m "mensagem clara e objetiva"
 git push origin main
```

Mostrar no final obrigatoriamente:
- branch final
- hash final
- resultado de git status
- confirmação de push

---

## BLOCO 2 — INSTRUÇÃO DA TAREFA

Descrever aqui claramente o objetivo técnico.

Exemplo:

Implemente Publish Receipt Engine:
- Criar publish_receipt.py
- Registrar timestamp
- Registrar media_id
- Registrar tipo
- Registrar legenda
- Registrar resposta da API
- Persistir JSON local
- Integrar com ace_bot.py
- Não quebrar funcionalidades existentes

---

Este template é lei operacional.
ACE Ω opera com disciplina de guerra.
