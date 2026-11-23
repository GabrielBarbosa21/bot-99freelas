"""Ponto de entrada unificado para execução do Bot 99Freelas."""

import sys
import argparse
import asyncio

from bot_99freelas.dashboard.cli_view import render_dashboard
from bot_99freelas.simulation import run_simulation
from bot_99freelas.cli import test_custom_project
from bot_99freelas.crawler.monitor import FreelasMonitor


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="bot_99freelas",
        description="🤖 Bot 99Freelas - Assistente Inteligente de Freelancing"
    )

    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: dashboard
    dash_parser = subparsers.add_parser("dashboard", help="Exibe o painel de métricas e quadro Kanban")
    dash_parser.add_argument("--cli", action="store_true", help="Exibe no terminal em vez de abrir interface web")

    # Comando: simulate
    subparsers.add_parser("simulate", help="Executa simulação de ponta a ponta com casos reais")

    # Comando: monitor
    subparsers.add_parser("monitor", help="Inicia o monitor assíncrono em background")

    # Comando: login
    subparsers.add_parser("login", help="Abre o navegador Chrome para login com Google e captura de sessão")

    # Comando: test
    test_parser = subparsers.add_parser("test", help="Testa avaliação e proposta de um projeto específico")
    test_parser.add_argument("--title", type=str, required=True, help="Título do projeto")
    test_parser.add_argument("--desc", type=str, required=True, help="Descrição do projeto")
    test_parser.add_argument("--min", type=float, default=200.0, help="Orçamento mínimo (BRL)")
    test_parser.add_argument("--max", type=float, default=400.0, help="Orçamento máximo (BRL)")
    test_parser.add_argument("--proposals", type=int, default=2, help="Propostas concorrentes já enviadas")
    test_parser.add_argument("--client", type=str, default="Cliente", help="Nome do cliente")

    args = parser.parse_args()

    if args.command == "dashboard":
        if getattr(args, "cli", False):
            render_dashboard()
        else:
            from bot_99freelas.dashboard.web import start_web_dashboard
            start_web_dashboard()
    elif args.command == "simulate":
        run_simulation()
    elif args.command == "monitor":
        monitor = FreelasMonitor()
        print("🚀 Iniciando monitor contínuo em background (Pressione Ctrl+C para encerrar)...")
        try:
            asyncio.run(monitor.run_loop())
        except KeyboardInterrupt:
            print("\n🛑 Monitor encerrado com sucesso.")
    elif args.command == "login":
        from bot_99freelas.crawler.browser_login import run_browser_login
        run_browser_login()
    elif args.command == "test":
        test_custom_project(
            title=args.title,
            description=args.desc,
            budget_min=args.min,
            budget_max=args.max,
            proposals_count=args.proposals,
            client_name=args.client,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
