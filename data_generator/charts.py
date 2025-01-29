import pandas as pd
import numpy as np
from plotnine import *

class ChartBuilder:

    def __init__(self):
        self.theme = theme(
            strip_background=element_rect(fill="white"),
            legend_title=element_blank(),
            legend_text=element_text(size=10, color="#474948"),
            legend_position=(0.5, 0.94),
            legend_direction="horizontal",
            legend_background=element_rect(fill="white", color="white"),
            legend_box_background=element_rect(fill="white", color="white"),
            axis_text_y=element_text(size=10, color="#474948"),
            axis_text_x=element_text(size=10, color="#474948"),
            text=element_text(family="sans", color="#474948", size=10),
            axis_title_x=(
                element_text(color='#474948', size=12, face="bold", margin={'t': 15})
            ),
            axis_title_y=(
                element_text(color='#474948', size=12, face="bold", margin={'r': 10})
            ),
            plot_title=(
                element_text(color='#474948', size=12, face="bold", margin={'b': 15, 'l':0}, ha='left', linespacing=1.5)
            ),
            axis_line = element_line(color="#C4C4C4", size=1, linetype="solid"),
            axis_ticks = element_line(color="#C4C4C4", size=1, linetype="solid"),
            panel_spacing=0.5,
            panel_background=element_rect(fill="white", color="white"),
            plot_background=element_rect(fill="white"),
            panel_grid_major_x=element_line(colour="white"),
            panel_grid_major_y=element_line(colour="white", linetype="dashed"),
            panel_grid_minor=element_blank(),
            #panel_border = element_rect(color="#373737"),
            strip_text_x=(
                element_text(size=12, hjust=0.5, color="#3A3C3B", face="bold")
            ),
            figure_size=(8, 6)
        )

    def build_bar_chart(self, data, c1):
        res = data.set_index(c1)
        
        if ('bias' in res.index.name) and ('rating' in res.index.name):
            name_map = {
                '-1': 'Inconclusive',
                '0': 'Not Biased',
                '1': 'Biased',
                '2': 'Very Biased',
                '1+2': 'Biased + Very Biased'
            }
            color_map = {
                'Inconclusive': '#CAC6C2',
                'Not Biased': '#f2eadf',
                'Biased': '#eb8483',
                'Very Biased': '#C22625',
                'Biased + Very Biased': '#7d2927'
            }
        elif ('bias' in res.index.name) and ('cat' in res.index.name):
            name_map = {
                'generalisation': 'Generalisation',
                'headline_or_imagery': 'Headline',
                'misrepresentation': 'Misrepresentation',
                'negative_behaviour': 'Negative Behaviour',
                'prominence': 'Omit Due Prominence'
            }
            color_map = {
                'Generalisation': '#4185A0',
                'Headline': '#AA4D71',
                'Misrepresentation': '#B85C3B',
                'Negative Behaviour': '#C5BE71',
                'Omit Due Prominence': '#7658A0'
            }
        else:
            name_map = dict(zip(res.columns.astype(str), res.columns.astype(str)))
            colors = ['#4185A0', '#AA4D71', '#B85C3B', '#C5BE71', '#7658A0']
            color_map = dict(zip(res.columns.astype(str), colors))
        
        
        # attr
        top_n = 5
        show_others = True
        show_inconclusive = True
        
        # def build_data_bar
        if top_n:
            # Get top n
            res = res.sort_values('count', ascending=False).reset_index()
            res.loc[:(top_n-1), 'group'] = 'top'
            res['group'] = res['group'].fillna('Others')
        
            # Collapse others
            res_top = res[res['group']=='top'].drop(columns=['group'])
            res_others = res[res['group']=='Others'].groupby('group')[['count']].transform('sum').drop_duplicates()
            res_others[c1] = 'Others'
        
        if show_others:
            res = pd.concat([res_top, res_others])
            res = res.ffill() # Fill missing B, VB, VBB article count
            # if ('bias' in c1) and ('cat') in c1:
            if 'VBB_unique_count' in res.columns:
                res['pct'] = (res['count']/res['VBB_unique_count']).fillna(0).multiply(100).round(1)
            else:
                res['pct'] = (res['count']/res['count'].sum()).fillna(0).multiply(100).round(1)
           
            res = res.set_index(c1)
        else:
            res = res_top
            # if ('bias' in c1) and ('cat') in c1:
            if 'VBB_unique_count' in res.columns:
                res['pct'] = (res['count']/res['VBB_unique_count']).fillna(0).multiply(100).round(1)
            else:
                res['pct'] = (res['count']/res['count'].sum()).fillna(0).multiply(100).round(1)
            res = res.set_index(c1)
        
        if not show_inconclusive:
            if 'Inconclusive' in res.index.astype(str).map(name_map):
                ind = list(res.index.astype(str).map(name_map)).index('Inconclusive')
                res = res.drop(columns=res.columns[ind])
        
        # Attach plot prerequisites
        res['name'] = res.index.astype(str).map(name_map).fillna('Others')
        res['name'] = pd.Categorical(values=res['name'], categories=['Others'] + list(name_map.values()), ordered=True)
        res['color'] = res['name'].astype(str).map(color_map).fillna('#e8e8e8')
        res['label'] = res['pct'].round(0).astype(int).astype(str) + '%'
        res['label'] = res['count'].astype(str) + ' (' + res['label'] + ')'

        p = (ggplot(res)
        + geom_bar(aes(x='name', y='count', fill='name'), stat='identity', width=0.60, show_legend=False)
        + geom_label(aes(x='name', y='count', label='label'), color="#474948", ha='center', size=8, show_legend=False)
        + scale_fill_manual(values=dict(zip(res['name'], res['color'])))
        + scale_y_continuous(limits=(0, res['count'].max()*1.10), labels=lambda l: ["%d" % int(v) for v in l])
        + ylab('Number of Articles')
        + xlab(c1.replace('_', ' ').title())
        + self.theme
        + coord_flip()
        )

        return p

    def build_heatmap_chart(self, data, c1, c2='bias_rating'):
        if 'bias' not in c2:
            raise ValueError('c2 only accepts bias_rating or bias_category. Please switch columns as needed.')
            
        res = data
        if ('bias' in res.index.name) and ('rating' in res.index.name):
            c1_name_map = {
                '-1': 'Inconclusive',
                '0': 'Not Biased',
                '1': 'Biased',
                '2': 'Very Biased',
                '1+2': 'Biased + Very Biased'
            }
        elif ('bias' in res.index.name) and ('cat' in res.index.name):
            c1_name_map = {
                'generalisation': 'Generalisation',
                'headline_or_imagery': 'Headline',
                'misrepresentation': 'Misrepresentation',
                'negative_behaviour': 'Negative Behaviour',
                'prominence': 'Omit Due Prominence'
            }
        else:
            c1_name_map = dict(zip(res.index.astype(str), res.index.astype(str)))

        if ('bias' in res.columns.name) and ('rating' in res.columns.name):
            c2_name_map = {
                '-1': 'Inconclusive',
                '0': 'Not Biased',
                '1': 'Biased',
                '2': 'Very Biased',
                '1+2': 'Biased + Very Biased'
            }
        elif ('bias' in res.columns.name) and ('cat' in res.columns.name):
            c2_name_map = {
                'generalisation': 'Generalisation',
                'headline_or_imagery': 'Headline',
                'misrepresentation': 'Misrepresentation',
                'negative_behaviour': 'Negative Behaviour',
                'prominence': 'Omit Due Prominence'
            }
        else:
            c2_name_map = dict(zip(res.columns.astype(str), res.columns.astype(str)))

        # attr
        top_n = 5
        show_others = False
        show_inconclusive = True

        if top_n:
            # Get top n
            res_x = res.sum(axis=1).sort_values(ascending=False).reset_index()
            res_x.columns = [c1, 'count']
            res_x.loc[:(top_n-1), 'group'] = 'top'
            res_x['group'] = res_x['group'].fillna('Others')

            # Get top n
            res_y = res.sum(axis=0).sort_values(ascending=False).reset_index()
            res_y.columns = [c2, 'count']
            res_y.loc[:(top_n-1), 'group'] = 'top'
            res_y['group'] = res_y['group'].fillna('Others')

            # Collapse others
            res_x_top = res_x[res_x['group']=='top'].drop(columns=['group'])
            res_y_top = res_y[res_y['group']=='top'].drop(columns=['group'])

            res.index = np.where(res.index.isin(res_x_top[c1].tolist()), res.index, 'Others')
            res.columns = [c if c in res_y_top[c2].tolist() else 'Others' for c in res.columns]
            res = res.groupby(res.index).sum().T.groupby(res.columns).sum().T

        if show_others:
            res = res.copy()
            res_pct = res.div(res.sum(axis=1), axis=0).fillna(0).multiply(100)
        else:
            if 'Others' in res.columns:
                res = res.drop(columns=['Others'])
            if 'Others' in res.index:
                res = res.drop(index=['Others'])

        if not show_inconclusive:
            if 'Inconclusive' in res.columns.astype(str).map(c2_name_map):
                ind = list(res.columns.astype(str).map(c2_name_map)).index('Inconclusive')
                res = res.drop(columns=res.columns[ind])
            if 'Inconclusive' in res.index.astype(str).map(c1_name_map):
                ind = list(res.index.astype(str).map(c1_name_map)).index('Inconclusive')
                res = res.drop(columns=res.columns[ind])

        # If df is filtered to include VBB articles only, denominator is the VBB unique count
        if 'VBB_unique_count' in res.columns:
            res_pct = res.div(res['VBB_unique_count'], axis=0).fillna(0).multiply(100)
            res_pct = res_pct.drop(['VBB_unique_count'], axis=1)
            VBB_unique_count = res['VBB_unique_count']

        # If all articles, denominator is across all articles
        else:
            res_pct = res.div(res.sum(axis=1), axis=0).fillna(0).multiply(100)

        res.index.name = c1
        res.columns.name = c2

        # With plot labels
        # print('VBB_unique_count?', 'VBB_unique_count' in res.columns)
        # print('res')
        # display(res)
        # print('res_pct')
        # display(res_pct)
        # print('---')
        res_label = res.drop(['VBB_unique_count'], axis=1, errors='ignore').astype(int).astype(str) + '\n(' + res_pct.round(0).astype(int).astype(str) + '%)'
        res_label.columns = [x.title() for x in res_label.columns.astype(str).map(c2_name_map).fillna('Others')] # No need to get sum of column names
        res_label['name'] = res_label.index.astype(str).map(c1_name_map).fillna('Others')
        if 'VBB_unique_count' in res.columns:
            res_label['name_label'] = res_label['name'].astype(str) + ' (' + VBB_unique_count.astype(int).astype(str) + ')'
        else:
            res_label['name_label'] = res_label['name'].astype(str) + ' (' + res.sum(axis=1).astype(int).astype(str) + ')'
        res_label['sort_index'] = res_label['name_label'].str.extract(r"\((\d+)\)", expand=False).sort_values()
        res_label = res_label.sort_values('sort_index')
        res_label = res_label.set_index('name_label').drop(columns=['name', 'sort_index'])

        # Do the same for res_pct
        res_pct['name'] = res_pct.index.astype(str).map(c1_name_map).fillna('Others')
        if 'VBB_unique_count' in res.columns:
            res_pct['name_label'] = res_pct['name'].astype(str) + ' (' + VBB_unique_count.astype(int).astype(str) + ')'
        else:
            res_pct['name_label'] = res_pct['name'].astype(str) + ' (' + res.sum(axis=1).astype(int).astype(str) + ')'
        res_pct['sort_index'] = res_pct['name_label'].str.extract(r"\((\d+)\)", expand=False).sort_values()
        res_pct = res_pct.sort_values('sort_index')
        res_pct = res_pct.set_index('name_label').drop(columns=['name', 'sort_index'])

        res_f = res_label.stack().reset_index()
        res_f.columns = [c1, c2, 'label']
        res_f['pct'] = res_pct.stack().reset_index().iloc[:, -1]
        res_f['pct'] = res_f['pct'].replace(0, np.nan)
        res_f['label'] = np.where(res_f['pct'].isna(), '', res_f['label'])
        res_f[c1] = pd.Categorical(res_f[c1], categories=[c for c in res_f[c1].drop_duplicates() if 'Others' in c] + [c for c in res_f[c1].drop_duplicates() if 'Others' not in c], ordered=True)
        res_f[c2] = pd.Categorical(res_f[c2], categories=[c for c in res_f[c2].drop_duplicates() if 'Others' in c] + [c for c in res_f[c2].drop_duplicates() if'Others' not in c], ordered=True)

        p =(ggplot(res_f)
        + geom_tile(aes(x=c2, y=c1, fill='pct'), color='white', size=1, show_legend=False)
        + geom_label(aes(x=c2, y=c1, label='label'), color="#474948", ha='center', size=8, show_legend=False)
        + scale_fill_gradientn(colors=['#EB8483', '#C22625'], na_value='#e8e8e8')
        + xlab(c2.replace('_', ' ').title())
        + ylab(c1.replace('_', ' ').title())
        + coord_equal()
        + coord_flip()
        + self.theme
        + theme(axis_text_x = element_text(rotation=45, hjust=1))
        )

        return p

    def build_odds_chart(self, data, c2):
        res = data.set_index(c2)

        if ('bias' in res.index.name) and ('rating' in res.index.name):
            name_map = {
                '-1': 'Inconclusive',
                '0': 'Not Biased',
                '1': 'Biased',
                '2': 'Very Biased',
                '1+2': 'Biased + Very Biased'
            }
            color_map = {
                'Inconclusive': '#CAC6C2',
                'Not Biased': '#f2eadf',
                'Biased': '#eb8483',
                'Very Biased': '#C22625',
                'Biased + Very Biased': '#7d2927'
            }
        elif ('bias' in res.index.name) and ('cat' in res.index.name):
            name_map = {
                'generalisation': 'Generalisation',
                'headline_or_imagery': 'Headline',
                'misrepresentation': 'Misrepresentation',
                'negative_behaviour': 'Negative Behaviour',
                'prominence': 'Omit Due Prominence'
            }
            color_map = {
                'Generalisation': '#4185A0',
                'Headline': '#AA4D71',
                'Misrepresentation': '#B85C3B',
                'Negative Behaviour': '#C5BE71',
                'Omit Due Prominence': '#7658A0'
            }
        else:
            name_map = dict(zip(res.columns.astype(str), res.columns.astype(str)))
            colors = ['#4185A0', '#AA4D71', '#B85C3B', '#C5BE71', '#7658A0']
            color_map = dict(zip(res.columns.astype(str), colors))

        # Attach plot prerequisites
        res['name'] = res.index.astype(str).map(name_map).fillna('Others')
        res['color'] = res['name'].astype(str).map(color_map).fillna('#e8e8e8')
        res['color'] = np.where(res['pvalue']<0.10, res['color'], '#4F5150')
        res['name_label'] = res['name'].astype(str) + ' (' + res['count'].astype(str) + ')'
        res['name_label'] = pd.Categorical(values=res['name_label'], categories=res['name_label'].drop_duplicates(), ordered=True)
        res['label'] = res['OR'].round(2)

        p = (ggplot(res)
        + geom_hline(yintercept=1, color='#e8e8e8', size=2)
        + geom_hline(yintercept=2, color='#e8e8e8', size=2)
        + geom_hline(yintercept=2, color='#e8e8e8', size=2)
        + geom_bar(aes(x='name_label', y='OR', fill='name'), stat='identity', width=0.60, show_legend=False)
        + geom_label(aes(x='name_label', y='OR', label='label'), color="#474948", ha='center', size=8, show_legend=False)
        + scale_fill_manual(values=dict(zip(res['name_label'], res['color'])))
        + scale_y_continuous(limits=(0, res['OR'].max()*1.10), labels=lambda l: ["%d" % int(v) for v in l])
        + ylab('Odds Ratio')
        + xlab(c2.replace('_', ' ').title())
        + annotate('text', x=res['name_label'].iloc[0], y=1, label='\n\n\n\n\n\n\nJust as likely', size=11, color='#4F5150')
        + annotate('text', x=res['name_label'].iloc[0], y=2, label='\n\n\n\n\n\n\nTwice as likely', size=11, color='#4F5150')
        + self.theme
        + coord_flip()
        )

        return p
