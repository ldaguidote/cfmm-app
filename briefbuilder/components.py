import os
import re
import shutil
from datetime import datetime
import pandas as pd

from llm_generator.generator import Generator
from llm_generator.fr_generator import FixedResponseGenerator
from data_generator.statistics import StatsCalculator
from data_generator.charts import ChartBuilder

class ReportComponentFactory:

    def __init__(self, query_params, query_data):
        self.query_data = self.__typecast_categorical_columns(query_data)
        self.stats      = StatsCalculator(query_params, self.query_data)
        self.llm_gen    = Generator(query_params, self.query_data)
        self.fr_gen     = FixedResponseGenerator(query_params, self.query_data)
        self.results    = dict()
        self.__initialize_components()

    def __initialize_components(self):
        self.component_report_parameters = ReportParametersComponent(self.stats, self.fr_gen)
        self.component_case_studies      = CaseStudyComponent(self.stats, self.fr_gen)
        self.component_pub_performance   = PublisherPerformanceComponent_withFixedResponses(self.stats, self.fr_gen)
        self.component_pub_comparison    = PubisherComparisonComponent_withFixedResponses(self.stats, self.fr_gen)
        self.component_conclusions       = ConclusionsComponent(self.stats, self.llm_gen)
        self.component_key_findings      = KeyFindingsComponent(self.stats, self.llm_gen)

    def __typecast_categorical_columns(self, query_data):
        """Turn query dataset into categorical type"""

        query_data['negative_aspects_score']    = pd.Categorical(query_data.negative_aspects_score, ordered=True, categories=['NA', 'Very Low', 'Low', 'Medium', 'High', 'Very High'])
        query_data['generalisation_score']      = pd.Categorical(query_data.generalisation_score, ordered=True, categories=['NA', 'Very Low', 'Low', 'Medium', 'High', 'Very High'])
        query_data['omit_due_prominence_score'] = pd.Categorical(query_data.omit_due_prominence_score, ordered=True, categories=['NA', 'Very Low', 'Low', 'Medium', 'High', 'Very High'])
        query_data['headline_bias_score']       = pd.Categorical(query_data.headline_bias_score, ordered=True, categories=['NA', 'Very Low', 'Low', 'Medium', 'High', 'Very High'])
        query_data['misrepresentation_score']   = pd.Categorical(query_data.misrepresentation_score, ordered=True, categories=['NA', 'Very Low', 'Low', 'Medium', 'High', 'Very High'])
        
        return query_data

    def __make_chart_tmp_folder(self):
        if not os.path.exists('tmp'):
            os.mkdir('tmp')
        else:
            shutil.rmtree('tmp')
            os.mkdir('tmp')

    def run(self):
        self.__make_chart_tmp_folder()
        self.build_component(self.component_report_parameters)
        self.build_component(self.component_case_studies)
        self.build_component(self.component_pub_performance)
        self.build_component(self.component_pub_comparison)
        self.build_component(self.component_conclusions)
        self.build_component(self.component_key_findings)
    
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
        # pattern = re.compile(r"""\[(.*?)\]\s*([\s\-A-Za-z0-9\.,\'’.%\"+]+)\s*""")
        pattern = re.compile(r"^\s*\[(.*?)\]\s*((?:\n|.)*)$")
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

class ReportParametersComponent(Component):

    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Report Parameters'
        self.schema = dict()


    def create_text(self):
        text = self.gen.generate_methodology()

        # British date formatting
        start_date = datetime.strptime(text['start_date'], '%Y-%m-%d').strftime('%d %B %Y')
        end_date = datetime.strptime(text['end_date'], '%Y-%m-%d').strftime('%d %B %Y')

        content = f"Publisher in Focus: {text['selected_publisher']}\n" \
                  f"Publisher Comparison: {text['compared_publishers']}\n" \
                  f"Report Coverage Dates: {start_date} to {end_date}\n" \
                  f"Topics: {text['topics']}" 
        self.text = content
    
    def consolidate_to_schema(self):
        self.schema = {
            self.component_name: {
                'title': self.component_name,
                'text': self.text
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
                'text': ''
            }
        }

    def build(self):
        # self.create_text()
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
                'text': ''
            }
        }

    def build(self):
        # self.create_text()
        self.consolidate_to_schema()


class PublisherPerformanceComponent_withFixedResponses(Component):
    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Publisher Performance Overview'
        self.valid_subsections = ['bias_rating', 'bias_category', 'bias_rating_vs_topics', 'bias_category_vs_topics']
        self.schema = dict()

    def create_subsection(self, subsection):
        chart = super()._chart_factory()

        if subsection in self.valid_subsections:
            chart_filepath = f'tmp/{subsection}.png'

            if subsection in ['bias_rating', 'bias_category']:

                # Use 2D biased stats functions if doing analysis by category
                if subsection == 'bias_rating':
                    data = self.stat.calc_1D_stats(subsection) 
                else:   
                    data = self.stat.calc_1D_biased_stats(subsection)
                
                chart_title = self.gen.generate_analysis(analysis_type=subsection, data=data)
                chart.build_bar_chart(data, subsection).save(chart_filepath)

            elif subsection in ['bias_rating_vs_topics', 'bias_category_vs_topics']:
                param = subsection.strip('_vs_topics')
                data = self.stat.calc_2D_biased_stats('topic', param)
                chart_title = self.gen.generate_analysis(analysis_type=subsection, data=data)
                chart.build_heatmap_chart(data, 'topic', param).save(chart_filepath)

            else:
                raise ValueError()
            
            subschema = self.consolidate_to_subschema(subsection, chart_filepath, chart_title, [''])
            return subschema
        
        else:
            raise ValueError('invalid subsection')
        
    def consolidate_to_subschema(self, subsection, chart_filepath, chart_title, bullets):
        title_dict = {
            'bias_rating': "Distribution of Bias Ratings", 
            'bias_category': "Distribution of Bias Categories",
            'bias_rating_vs_topics': "Distribution of Bias Ratings vs Topics", 
            'bias_category_vs_topics': "Distribution of Bias Categories vs Topics", 
        }

        subschema = {
            subsection: {
                'title': title_dict[subsection],
                'chart_title': chart_title,
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


class PubisherComparisonComponent_withFixedResponses(Component):

    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Publisher Comparison'
        self.valid_subsections = ['bias_rating_comparison', 'bias_category_comparison']
        
        self.schema = dict()

    def create_subsection(self, subsection):
        chart = super()._chart_factory()

        if subsection in self.valid_subsections:
            chart_filepath = f'tmp/{subsection}.png'

            param = subsection.removesuffix('_comparison')
            data = self.stat.calc_1D_stats(param, include_compared_publishers=True)
            chart_title = self.gen.generate_analysis(analysis_type=subsection, data=data)
            chart.build_stacked_bar_chart(data, param).save(chart_filepath)
        
            subschema = self.consolidate_to_subschema(subsection, chart_filepath, chart_title, [''])
            return subschema
        
        else:
            raise ValueError('invalid subsection')
        
    def consolidate_to_subschema(self, subsection, chart_filepath, chart_title, bullets):
        title_dict = {
            'bias_rating_comparison': "Bias Rating Comparison",
            'bias_category_comparison': "Bias Category Comparison"
        }

        subschema = {
            subsection: {
                'title': title_dict[subsection],
                'chart_title': chart_title,
                'chart_filepath': chart_filepath,
                'bullets': bullets[0]
            }
        }
        return subschema
    
    def build(self):
        self.schema[self.component_name] = self.create_subsection('bias_rating_comparison')
        self.schema[self.component_name].update(self.create_subsection('bias_category_comparison'))


class PublisherPerformanceComponent(Component):

    def __init__(self, statistics_object, generator_object):
        super().__init__(statistics_object, generator_object)
        self.component_name = 'Publisher Performance Overview'
        self.valid_subsections = ['bias_rating', 'bias_category', 'bias_rating_vs_topics', 'bias_category_vs_topics']
        self.schema = dict()
    
    def create_subsection(self, subsection):
        chart = super()._chart_factory()

        if subsection in self.valid_subsections:
            chart_filepath = f'tmp/{subsection}.png'

            if subsection in ['topic', 'bias_rating', 'bias_category']:

                # Use 2D biased stats functions if doing analysis by category
                if subsection == 'bias_rating':
                    data = self.stat.calc_1D_stats(subsection) 
                else:   
                    data = self.stat.calc_1D_biased_stats(subsection)
                
                text = self.gen.generate_analysis(analysis_type=subsection, data=data)
                chart.build_bar_chart(data, subsection).save(chart_filepath)

            elif subsection in ['bias_rating_vs_topics', 'bias_category_vs_topics']:
                param = subsection.strip('_vs_topics')
                data = self.stat.calc_2D_biased_stats(param)
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
            'bias_rating': "Distribution of Bias Ratings", 
            'bias_category': "Distribution of Bias Categories",
            'bias_rating_vs_topics': "Distribution of Bias Ratings vs Topics", 
            'bias_category_vs_topics': "Distribution of Bias Categories vs Topics", 
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
        self.valid_subsections = ['Misrepresentation', 'Due Prominence', 'Negative Behaviour',
                                  'Generalisation', 'Imagery and Headlines']
        
        self.schema = dict()

    def create_subsection(self, subsection):
        if subsection in self.valid_subsections:
            response_list = self.gen.generate_case_study(case_type=subsection)

            # If no case studies of the type is found, return an empty list, else return the subschema
            if len(response_list) == 0 or response_list == None:
                return {subsection: ["There are no more case studies for this bias category."]}
            else:
                article_titles_list, bullets_list = [], []
                for response in response_list:
                    article_titles, bullets = super()._parse_response(response)
                    print(article_titles)
                    article_titles_list.append(article_titles[0])
                    bullets_list.append(bullets[0])
                
                subschema = self.consolidate_to_subschema(subsection, article_titles_list, bullets_list)
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
        # self.schema[self.component_name] = self.create_subsection('Very Biased')
        # self.schema[self.component_name].update(self.create_subsection('Biased'))
        
        self.schema[self.component_name] = self.create_subsection('Misrepresentation')
        self.schema[self.component_name].update(self.create_subsection('Due Prominence'))
        self.schema[self.component_name].update(self.create_subsection('Negative Behaviour'))
        self.schema[self.component_name].update(self.create_subsection('Generalisation'))
        self.schema[self.component_name].update(self.create_subsection('Imagery and Headlines'))