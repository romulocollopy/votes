#!/usr/bin/env python
# coding: utf:8

import csv
import requests
from xml.etree import ElementTree as ET
from xml.etree.ElementTree import Element


class ProposalsParser:

    def request_proposals(self, year=2015):
        proposals_url = (
            u'http://www.camara.gov.br/' +
            'SitCamaraWS/Proposicoes.asmx/' +
            'ListarProposicoesVotadasEmPlenario?ano={}&tipo=').format(year)
        self.response = requests.get(proposals_url)

    def get_xml_content(self):
        try:
            raw_xml = self.response.content
        except AttributeError:
            self.request_proposals()
            raw_xml = self.response.content

        self.xml = ET.fromstring(raw_xml)

    def parse_xml(self):
        tmp_list = []
        for proposicao in self.xml.findall('proposicao'):
            tmp_list += [
                dict(
                    code = int(proposicao.find('codProposicao').text),
                    name = proposicao.find('nomeProposicao').text,
                    date = proposicao.find('dataVotacao').text,
                    year = proposicao.find('nomeProposicao').text.split('/')[1],
                    type = proposicao.find('nomeProposicao').text.split()[0],
                    number = proposicao.find('nomeProposicao').text.split()[1].split('/')[0],
                )
            ]
        pro_dict = {i['code']: i for i in tmp_list}
        self.proposals_list = list(pro_dict.values())


    def write_to_csv(self):

        with open('proposals.csv', 'w', newline='') as csvfile:
            fieldnames = self.proposals_list[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for prop in self.proposals_list:
                writer.writerow(prop)


class VoteParser:

    def __init__(self, proposal_list):
        self.proposals_list = proposal_list

    def request_vote(self, proposal_dict):
        year = proposal_dict['year']
        type = proposal_dict['type']
        number = proposal_dict['number']

        votes_url = (
            'http://www.camara.gov.br/SitCamaraWS/Proposicoes.asmx/' +
            'ObterVotacaoProposicao?' +
            'tipo={tipo}&numero={numero}&ano={ano}').format(
                tipo=type,
                ano=year,
                numero=number
            )
        self.response = requests.get(votes_url)

    def get_xml_content(self):
        try:
            raw_xml = self.response.content
        except AttributeError:
            self.request_proposals()
            raw_xml = self.response.content

        self.xml = ET.fromstring(raw_xml)

    def parse_xml(self):
        tmp_list = []
        deputados = self.xml.find('Votacoes').find('Votacao').find('votos').findall('Deputado')
        for deputado in deputados:
            tmp_list += [
                dict(
                    nome = str.decode(deputado.get('Nome').encode('utf-8')),
                    ide_cadastro = deputado.get('ideCadastro'),
                    partido = deputado.get('Partido'),
                    uf = deputado.get('UF'),
                    voto = str.decode(deputado.get('Voto').encode('utf-8')),
                )
            ]
        pro_dict = {i['ide_cadastro']: i for i in tmp_list}
        self.votes_list = list(pro_dict.values())

    def write_to_csv(self):

        with open('votes.csv', 'w', newline='') as csvfile:
            fieldnames = self.votes_list[0].keys()
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for vote in self.votes_list:
                writer.writerow(vote)


import unittest

class ProsposicoesTest(unittest.TestCase):

    def setUp(self):
        p = ProposalsParser()
        p.request_proposals()
        self.proposals = p

    def test_get_content(self):
        self.assertEqual(200, self.proposals.response.status_code)

    def test_get_xml_content(self):
        p = self.proposals
        p.get_xml_content()
        self.assertIsInstance(p.xml, Element)

    def test_list_of_proposals(self):
        self.proposals.get_xml_content()
        self.proposals.parse_xml()
        self.assertIsInstance(self.proposals.proposals_list, list)
        self.assertIsInstance(self.proposals.proposals_list[0], dict)
        self.assertIn('code', self.proposals.proposals_list[0])
        self.assertIn('name', self.proposals.proposals_list[0])
        self.assertIn('date', self.proposals.proposals_list[0])

    def test_write_file(self):
        self.proposals.get_xml_content()
        self.proposals.parse_xml()
        self.proposals.write_to_csv()

    def test_get_votes(self):
        self.proposals.get_xml_content()
        self.proposals.parse_xml()

        v = VoteParser(self.proposals.proposals_list)
        v.request_vote(v.proposals_list[0])
        v.get_xml_content()
        v.parse_xml()
        v.write_to_csv()



unittest.main()
