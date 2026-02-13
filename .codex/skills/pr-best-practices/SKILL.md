---
name: pr-best-practices
description: Buenas practicas para preparar y abrir Pull Requests (PRs). Usa cuando alguien pida ayuda para armar un PR, redactar la descripcion del PR o revisar que un PR este listo para merge.
---

# PR Best Practices

## Objetivo
Ayudar a preparar PRs claros, revisables y faciles de mergear.

## Flujo recomendado
1. Entender el objetivo del cambio y el impacto esperado.
2. Proponer un alcance acotado: un PR = un tema.
3. Verificar calidad minima antes de abrir:
- Compila o ejecuta sin errores.
- Tests relevantes corren o se explica por que no.
- Documentacion o comentarios actualizados si aplica.
4. Redactar la descripcion del PR con formato consistente.

## Checklist de calidad
- Cambios minimos y enfocados.
- Mensajes de commit claros.
- No hay archivos generados o binarios innecesarios.
- Riesgos y tradeoffs explicitos.
- Pasos de verificacion claros.

## Formato sugerido de descripcion de PR
- **Resumen**: que cambia y por que.
- **Contexto**: problema u objetivo.
- **Cambios principales**: lista corta.
- **Pruebas**: comandos ejecutados o motivo si no aplica.
- **Riesgos**: areas sensibles o impacto.
- **Notas**: migraciones, flags, o pasos post-merge.

## Si falta informacion
Pedir datos concretos: objetivo, alcance, comandos de test, y riesgos percibidos.
