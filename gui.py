import re

from prompt_toolkit.application import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import WordCompleter, Completer, Completion
from prompt_toolkit.contrib.regular_languages.compiler import compile
from prompt_toolkit.contrib.regular_languages.completion import GrammarCompleter
from prompt_toolkit.contrib.regular_languages.lexer import GrammarLexer
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout, HSplit, CompletionsMenu, FloatContainer, Float
from prompt_toolkit.lexers import SimpleLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea, SearchToolbar

from exceptions import AbortCommand
from models import STORE
from tools import existing_branches, existing_databases


def serve():
    kb = KeyBindings()
    @kb.add("c-c")
    def _(event):
        if input_prompt.text:
            input_prompt.text = ''
        else:
            event.app.exit()

    grammar = compile(' | '.join(
        f"(\s* {command.pattern} \s*)"
        for command in STORE.commands.values()
    ))

    class BranchCompleter(Completer):
        def get_completions(self, document, complete_event):
            for branch in existing_branches():
                if re.match(document.text.replace('%', '.*'), branch):
                    yield Completion(branch, -len(branch))

    class DatabaseCompleter(Completer):
        def get_completions(self, document, complete_event):
            for base in existing_databases():
                if re.match(document.text.replace('%', '.*'), base):
                    yield Completion(base, -len(base))

    class RepoCompleter(Completer):
        def get_completions(self, document, complete_event):
            for repo_name in STORE.repositories:
                if repo_name.startswith(document.text):
                    yield Completion(repo_name, -len(repo_name))

    def accept(buff: Buffer):
        vars = grammar.match(buff.text)
        if not vars:
            return True
        vars = vars.variables()
        output.text = f"{vars}"
        command = vars['command']
        try:
            if command not in STORE.commands:
                raise AbortCommand('Invalid command')
            output.text = ''
            STORE.commands[command].callback(vars)
        except AbortCommand as e:
            output.text = f"{e}"
            return True
        return False

    input_prompt = TextArea(
        prompt=">>> ",
        height=1,
        multiline=False,
        style="class:input-field",
        search_field=SearchToolbar(),
        accept_handler=accept,
        completer=GrammarCompleter(grammar, {
            'command': WordCompleter(
                meta_dict=(meta_dict :={
                    command.name: command.help
                    for command in STORE.commands.values()
                }),
                words=list(meta_dict),
            ),
            'base': WordCompleter(list(STORE.bases)),
            'force': WordCompleter(['--force']),
            'target': BranchCompleter(),
            'database': DatabaseCompleter(),
            'repo': RepoCompleter(),
        }),
        lexer=GrammarLexer(
            grammar,
            lexers={
                'command': SimpleLexer('class:command'),
            }
        ),
        complete_while_typing=True,
    )
    output = TextArea(style="class:output-field")
    root_container = FloatContainer(
        content=HSplit([
            input_prompt,
            output,
        ]),
        floats=[
            Float(
                xcursor=True,
                ycursor=True,
                content=CompletionsMenu(max_height=16, scroll_offset=1),
            ),
        ],
    )

    application = Application(
        layout=Layout(container=root_container),
        key_bindings=kb,
        style=Style([
            ("output-field", "bg:#000044 #ffffff"),
            ("input-field", "bg:#000000 #ffffff"),
            ("command", "fg:#ff0066"),
        ]),
        full_screen=True,
    )
    application.run()
