class ShortcutManager:
    """Registro central e persistência dos atalhos do Serifa Music."""

    ACTIONS = (
        ("next_track", "Reprodução", "Avançar faixa", ("L",)),
        ("play_pause", "Reprodução", "Pausar / continuar reprodução", ("K", "Space")),
        ("previous_or_restart", "Reprodução", "Voltar para a faixa anterior", ("J",)),
        ("restart_track", "Reprodução", "Reiniciar faixa atual", ("R",)),
        ("volume_up", "Reprodução", "Aumentar volume", ("Ctrl+Up",)),
        ("volume_down", "Reprodução", "Diminuir volume", ("Ctrl+Down",)),
        ("shuffle", "Reprodução", "Ativar / desativar reprodução aleatória", ("Ctrl+R",)),
        ("repeat", "Reprodução", "Alternar modo Repeat", ("Ctrl+Shift+R",)),
        ("infinite_play", "Reprodução", "Ativar / desativar Infinite Play", ("I",)),
        ("seek_back_5", "Reprodução", "Voltar 5 segundos", ("Left",)),
        ("seek_forward_5", "Reprodução", "Avançar 5 segundos", ("Right",)),
        ("seek_back_10", "Reprodução", "Voltar 10 segundos", ("Ctrl+Left",)),
        ("seek_forward_10", "Reprodução", "Avançar 10 segundos", ("Ctrl+Right",)),
        ("seek_percentage", "Reprodução", "Pular para 10%–90% da faixa", tuple(str(i) for i in range(1, 10))),
        ("mute", "Reprodução", "Ativar / desativar mudo", ("Ctrl+M",)),
        ("favorite_selected", "Favoritos", "Favoritar faixa selecionada", ("F",)),
        ("favorite_current", "Favoritos", "Favoritar faixa em reprodução", ("C",)),
        ("home", "Navegação", "Abrir tela inicial", ("Ctrl+H",)),
        ("favorites", "Navegação", "Abrir Favoritos", ("Ctrl+B",)),
        ("play_favorites", "Navegação", "Reproduzir Favoritos", ("Ctrl+Shift+B",)),
        ("global_search", "Navegação", "Abrir pesquisa", ("Ctrl+F",)),
        ("import", "Navegação", "Abrir Importação", ("Ctrl+I",)),
        ("fullscreen", "Navegação", "Ativar / desativar tela cheia", ("F11",)),
        ("queue_panel", "Fila e playlists", "Abrir / fechar fila de reprodução", ("Ctrl+P",)),
        ("remove_playlist_track", "Fila e playlists", "Remover faixa da playlist atual", ("Backspace",)),
        ("remove_queue_track", "Fila e playlists", "Remover faixa selecionada da fila", ("Delete",)),
        ("new_playlist", "Fila e playlists", "Criar nova playlist", ("Ctrl+Shift+N",)),
        ("play_selected", "Fila e playlists", "Reproduzir faixa selecionada", ("Return",)),
        ("equalizer", "Recursos adicionais", "Abrir / fechar Equalizador", ("Ctrl+E",)),
        ("next_preview", "Recursos adicionais", "Ativar / desativar prévia da próxima faixa", ("Ctrl+Shift+P",)),
        ("settings", "Recursos adicionais", "Abrir Configurações", ("Ctrl+,",)),
        ("about", "Recursos adicionais", "Abrir Sobre", ("F1",)),
        ("context_escape", "Navegação", "Fechar tela cheia ou pesquisa", ("Escape",)),
        ("search_up", "Navegação", "Resultado anterior na pesquisa", ("Up",)),
        ("search_down", "Navegação", "Próximo resultado na pesquisa", ("Down",)),
    )

    def __init__(self, settings):
        self.settings = settings

    @staticmethod
    def _normalize(binding):
        return " ".join(str(binding).strip().split()).casefold()

    def get_bindings(self, action_id):
        action = next(
            (item for item in self.ACTIONS if item[0] == action_id),
            None
        )
        if action is None:
            raise KeyError(f"Atalho desconhecido: {action_id}")

        stored = self.settings.value(
            f"shortcuts/{action_id}",
            list(action[3]),
            type=list
        )

        if isinstance(stored, str):
            stored = [stored]

        return [
            str(value)
            for value in (stored or [])
            if str(value).strip()
        ]

    def all_actions(self):
        return [
            {
                "id": action_id,
                "category": category,
                "description": description,
                "defaults": list(defaults),
                "bindings": self.get_bindings(action_id),
            }
            for action_id, category, description, defaults in self.ACTIONS
        ]

    def find_conflict(self, binding, exclude_action=None):
        normalized = self._normalize(binding)

        if not normalized:
            return None

        for action in self.all_actions():
            if action["id"] == exclude_action:
                continue

            if any(
                self._normalize(current) == normalized
                for current in action["bindings"]
            ):
                return action

        return None

    def set_bindings(self, action_id, bindings):
        known_ids = {action[0] for action in self.ACTIONS}

        if action_id not in known_ids:
            raise KeyError(f"Atalho desconhecido: {action_id}")

        cleaned = []
        seen = set()

        for binding in bindings:
            value = str(binding).strip()
            normalized = self._normalize(value)

            if not normalized:
                continue

            if normalized in seen:
                raise ValueError(f"Combinação repetida: {value}")

            conflict = self.find_conflict(
                value,
                exclude_action=action_id
            )

            if conflict:
                raise ValueError(
                    f"{value} já está associado a: "
                    f"{conflict['description']}"
                )

            seen.add(normalized)
            cleaned.append(value)

        self.settings.setValue(
            f"shortcuts/{action_id}",
            cleaned
        )
        self.settings.sync()

    def reset_binding(self, action_id):
        if not any(action[0] == action_id for action in self.ACTIONS):
            raise KeyError(f"Atalho desconhecido: {action_id}")

        self.settings.remove(f"shortcuts/{action_id}")
        self.settings.sync()

    def reset_all(self):
        self.settings.remove("shortcuts")
        self.settings.sync()
