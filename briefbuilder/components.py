import os
import re
import shutil

from llm_generator.generator import Generator
from data_generator.statistics import StatsCalculator
from data_generator.charts import ChartBuilder

class ReportComponentFactory:

    def __init__(self, query_params, query_data):
        self.stats = StatsCalculator(query_params, query_data)
        self.gen = Generator(query_params, query_data)
        self.results = dict()

    def __make_chart_tmp_folder(self):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        else:
            shutil.rmtree('tmp')
            os.mkdir('tmp')

    def run(self):
        self.__make_chart_tmp_folder()
        self.build_component(MethodologyComponent(self.stats, self.gen))
        self.build_component(CaseStudyComponent(self.stats, self.gen))
        self.build_component(PubisherPerformanceComponent(self.stats, self.gen))
        self.build_component(PubisherComparisonComponent(self.stats, self.gen))
        self.build_component(ConclusionsComponent(self.stats, self.gen))
        self.build_component(KeyFindingsComponent(self.stats, self.gen))
    
    def build_component(self, component_object):
        component_object.build()
        self.results.update(component_object.schema)


class Component:

    def __init__(self, statistics_object, generator_object):
        self.stat = statistics_object
        self.gen = generator_object
        self.component_name = None
        self.schema = dict()

    def _chart_factory(self):
        return ChartBuilder()
    
    def _parse_response(self, llm_response):
        pattern = re.compile(r"""\[(.*?)\]\s*([\s\-A-Za-z0-9\.,\'’.%]+)\s*""")
        # pattern = re.compile(r"""\[(.*?)\]\s*(.*)\s*""")
        parsed_response = re.findall(pattern, llm_response)
        
        titles = [i[0] for i in parsed_response]
        bullets = [i[1] for i in parsed_response]
        bullets = ['\n'.join(b.strip('- ').split('  \n- ')) for b in bullets]
        
        return titles, bullets


class MethodologyComponent(Component):

    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Methodology'
        self.schema = dict()


    def create_text(self):
        text = self.gen.generate_methodology()
        _, content = super()._parse_response(text)
        self.text = content
    
    def consolidate_to_schema(self):
        self.schema = {
            self.component_name: {
                'title': self.component_name,
                'text': self.text[0]
            }
        }

    def build(self):
        self.create_text()
        self.consolidate_to_schema()


class KeyFindingsComponent(Component):

    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Key Findings'
        self.schema = dict()


    def create_text(self):
        text = self.gen.generate_key_message()
        _, content = super()._parse_response(text)
        self.text = content
    
    def consolidate_to_schema(self):
        self.schema = {
            self.component_name: {
                'title': self.component_name,
                'text': self.text[0]
            }
        }

    def build(self):
        self.create_text()
        self.consolidate_to_schema()


class ConclusionsComponent(Component):

    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Conclusions'
        self.schema = dict()


    def create_text(self):
        text = self.gen.generate_conclusions()
        _, content = super()._parse_response(text)
        self.text = content
    
    def consolidate_to_schema(self):
        self.schema = {
            self.component_name: {
                'title': self.component_name,
                'text': self.text[0]
            }
        }

    def build(self):
        self.create_text()
        self.consolidate_to_schema()


class PubisherPerformanceComponent(Component):

    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Publisher Performance Overview'
        self.valid_subsections = ['topic', 'bias_rating', 'bias_category', 'bias_rating_vs_topics', 'bias_category_vs_topics']
        self.schema = dict()
    
    def create_subsection(self, subsection):
        chart = super()._chart_factory()

        if subsection in self.valid_subsections:
            chart_filepath = f'tmp/{subsection}.png'

            if subsection in ['topic', 'bias_rating', 'bias_category']:
                data = self.stat.calc_1D_stats(subsection)
                text = self.gen.generate_analysis(analysis_type=subsection, data=data)
                chart.build_bar_chart(data, subsection).save(chart_filepath)

            elif subsection in ['bias_rating_vs_topics', 'bias_category_vs_topics']:
                param = subsection.strip('_vs_topics')
                data = self.stat.calc_2D_stats(param)
                text = self.gen.generate_analysis(analysis_type=param, data=data)
                chart.build_heatmap_chart(data, param).save(chart_filepath)

            else:
                raise ValueError()
            
            chart_title, bullets = super()._parse_response(text)
        
            subschema = self.consolidate_to_subschema(subsection, chart_filepath, chart_title, bullets)
            return subschema
        
        else:
            raise ValueError('invalid subsection')

    def consolidate_to_subschema(self, subsection, chart_filepath, chart_title, bullets):
        title_dict = {
            'topic': "Topic Coverage for All Publication",
            'bias_rating': "Analysis of Bias Ratings", 
            'bias_category': "Analysis of Bias Categories",
            'bias_rating_vs_topics': "Analysis of Bias Ratings vs Topics", 
            'bias_category_vs_topics': "Analysis of Bias Categories vs Topics", 
        }

        subschema = {
            subsection: {
                'title': title_dict[subsection],
                'chart_title': chart_title[0],
                'chart_filepath': chart_filepath,
                'bullets': bullets[0]
            }
        }
        return subschema

    def build(self):
        self.schema[self.component_name] = self.create_subsection('bias_rating')
        self.schema[self.component_name].update(self.create_subsection('bias_category'))
        self.schema[self.component_name].update(self.create_subsection('bias_rating_vs_topics'))
        self.schema[self.component_name].update(self.create_subsection('bias_category_vs_topics'))


class PubisherComparisonComponent(Component):

    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Publisher Comparison'
        self.valid_subsections = ['tendency_bias_rating', 'tendency_bias_category']
        
        self.schema = dict()

    def create_subsection(self, subsection):
        chart = super()._chart_factory()

        if subsection in self.valid_subsections:
            chart_filepath = f'tmp/{subsection}.png'

            param = subsection.removeprefix('tendency_')
            data = self.stat.calc_tendency(param)
            text = self.gen.generate_analysis(analysis_type='tendency', data=data)
            chart.build_odds_chart(data, param).save(chart_filepath)

            chart_title, bullets = super()._parse_response(text)
        
            subschema = self.consolidate_to_subschema(subsection, chart_filepath, chart_title, bullets)
            return subschema
        
        else:
            raise ValueError('invalid subsection')
        
    def consolidate_to_subschema(self, subsection, chart_filepath, chart_title, bullets):
        title_dict = {
            'tendency_bias_rating': "Analyzing Publisher's Tendency to Commit Bias",
            'tendency_bias_category': "Analyzing Publisher's Tendency to Commit Certain Biases (by Category)"
        }

        subschema = {
            subsection: {
                'title': title_dict[subsection],
                'chart_title': chart_title[0],
                'chart_filepath': chart_filepath,
                'bullets': bullets[0]
            }
        }
        return subschema
    
    def build(self):
        self.schema[self.component_name] = self.create_subsection('tendency_bias_rating')
        self.schema[self.component_name].update(self.create_subsection('tendency_bias_category'))


class CaseStudyComponent(Component):
    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Case Studies'
        self.valid_subsections = ['Very Biased', 'Biased', 'Misrepresentation', 'Due Prominence', 'Negative Behaviour',
                                  'Generalisation', 'Imagery and Headlines']
        
        self.schema = dict()

    def create_subsection(self, subsection, n_examples=1):
        if subsection in self.valid_subsections:
            text = self.gen.generate_case_study(case_type=subsection, n_examples=n_examples)

            # If no case studies of the type is found, return an empty list, else return the subschema
            if text == None:
                return {subsection: []}
            else:
                article_titles, bullets = super()._parse_response(text)
                subschema = self.consolidate_to_subschema(subsection, article_titles, bullets)
                return subschema
        
        else:
            raise ValueError('invalid subsection')
        
    def consolidate_to_subschema(self, subsection, article_titles, bullets):
        articles = list(zip(article_titles, bullets))
        article_list = [{'title': article[0], 'bullets': article[1]} for article in articles]

        subschema = {
            subsection: article_list
        }
        return subschema
    
    def build(self):
        self.schema[self.component_name] = self.create_subsection('Very Biased')
        self.schema[self.component_name].update(self.create_subsection('Biased'))
        self.schema[self.component_name].update(self.create_subsection('Misrepresentation'))
        self.schema[self.component_name].update(self.create_subsection('Due Prominence'))
        self.schema[self.component_name].update(self.create_subsection('Negative Behaviour'))
        self.schema[self.component_name].update(self.create_subsection('Generalisation'))
        self.schema[self.component_name].update(self.create_subsection('Imagery and Headlines'))