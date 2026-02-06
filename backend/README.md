# IPTV Backend - Gestion des comptes

## Ajouter un compte IPTV

Deux options sont disponibles (mêmes champs `host`, `username`, `password`) :

- `POST /account` : enregistre le compte localement **et** l'active immédiatement.
- `POST /login` : active le compte et tente aussi une sauvegarde locale (pour compatibilité UI).

Une fois le compte enregistré, il reste disponible après redémarrage grâce à l'auto-login.

## Où sont stockés les credentials ?

Les credentials sont stockés localement dans :

```
backend/app/data/credentials.json
```

Ce fichier est **ignoré par Git** (`.gitignore`) afin d'éviter tout commit accidentel.

## Pourquoi ce fichier n'est pas dans Git ?

Les credentials IPTV sont sensibles. Ils ne doivent jamais être versionnés ni partagés.
Le fichier est donc stocké localement et explicitement exclu des commits.

## Workflow recommandé

1. `POST /account` (ou `POST /login`) pour enregistrer le compte.
2. `POST /refresh` pour lancer le rafraîchissement du cache.
3. `GET /channels` pour récupérer les chaînes.
4. `GET /status` pour vérifier l'état (`logged_in`, cache, etc.).

## Notes importantes

- Le mot de passe n'est **jamais** renvoyé par l'API.
- Les logs utilisent des marqueurs clairs (`[ACCOUNT]`, `[REFRESH]`) pour le debug.
