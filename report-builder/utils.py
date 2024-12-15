import pandas as pd
from plotnine import *
import numpy as np
import scipy.stats as stats

proj_theme = theme(
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

biasrating_colors = ['#CAC6C2', '#f2eadf', '#eb8483', '#C22625']
default_colors = ['#4185A0', '#AA4D71', '#B85C3B', '#C5BE71', '#7658A0']

def show_counts_c1(df_corpus, publisher, c1):
    """Shows counts for one dimension

    Accepted values for dimension:
    'location', 'bias_rating', 'bias_categories', 'topic'
    """
    # Filter publisher
    df_publisher = df_corpus[df_corpus['publisher']==publisher]
    # List possible C1 options that can use group by
    simple_c1 = ['location', 'bias_rating']

    if c1 in simple_c1:
        # Group by c1
        df_count = df_publisher.groupby(c1).size().reset_index(name='count')
        return df_count

    elif c1 == 'bias_category':
        # Prepare expected bias categories
        expected_categories = {
            'generalisation',
            'prominence',
            'negative_behaviour',
            'misrepresentation',
            'headline_or_imagery'
        }
        # Find bias categories that are present in dataframe
        actual_categories = list(set(df_publisher.columns).intersection(expected_categories))
        df_count = df_publisher[actual_categories].sum().rename_axis(c1).reset_index(name='count')
        return df_count

    elif c1 == 'topic':
        # Prepare exploded topics
        s_topics = df_publisher[c1].apply(lambda x: x.split(" | "))
        df_count = s_topics.explode().reset_index().groupby(c1).size().reset_index(name='count')
        df_count = df_count.replace('', 'Unknown')
        return df_count

    else:
        raise ValueError(f"Unknown category: {c1}")
    
def show_counts_c1c2(df_corpus, publisher, c1, c2):
    """Shows counts for two dimensions

    Accepted values for dimensions:
    'location', 'bias_rating', 'bias_category', 'topic'
    """
    ## Filter articles by publisher
    df_publisher = df_corpus[df_corpus['publisher']==publisher]
    simple_c1_c2 = ['location', 'bias_rating']
    advanced_c1_c2 = ['topic', 'bias_category']
    if c1 in simple_c1_c2 + advanced_c1_c2 or c2 in simple_c1_c2 + advanced_c1_c2:
        if c1 not in simple_c1_c2 or c2 not in simple_c1_c2:
            if c1 == 'topic' or c2 == 'topic':
                # Split topic list
                df_publisher['topic'] = df_publisher['topic'].apply(lambda x: x.split(" | "))
                # Explode into singular topics
                df_publisher = df_publisher.explode('topic')

            if c1 == 'bias_category' or c2 == 'bias_category':
                # Prepare expected bias categories
                expected_categories = {
                    'generalisation',
                    'prominence',
                    'negative_behaviour',
                    'misrepresentation',
                    'headline_or_imagery'
                }
                # Find bias categories that are present in dataframe
                actual_categories = list(set(df_publisher.columns).intersection(expected_categories))
                # Detect other dimension other than bias categories
                c1_c2 = [c1, c2]
                c1_c2.remove("bias_category")
                # Melt bias categories into one column
                df_publisher = df_publisher.melt(
                    id_vars=c1_c2.pop(),
                    value_vars=actual_categories,
                    var_name="bias_category",
                    value_name="count"
                )
    else:
        raise ValueError(f"Either one or both of the categories are unknown: {c1}, {c2}")

    if c1 == 'bias_category' or c2 == 'bias_category':
        df_count = df_publisher.groupby([c1, c2]).sum().reset_index()
    else:
        df_count = df_publisher.groupby([c1, c2]).size().reset_index(name='count')
    df_count = df_count.replace('', 'Unknown')
    df_count = df_count.pivot(index=c1, columns=c2, values='count')
    df_count = df_count.fillna(0)
    return df_count

def show_odds(df_corpus, selected_publisher, compared_publishers, c2):
    """Shows odds ratio for bias rating and category

    Accepted values for dimensions:
    'bias_rating', 'bias_category'
    """
    # Filter articles by stated publishers
    df_all = df_corpus[df_corpus['publisher'].isin([selected_publisher]+compared_publishers)]
    df_all['publisher'] = df_all['publisher'].replace(compared_publishers, 'Others')

    if c2 == "bias_rating":
        # Filter out negative bias rating
        df_all = df_all[df_all['bias_rating']!=-1]
        value_list = df_all['bias_rating'].unique().tolist()
        df_all = pd.get_dummies(df_all[["publisher","bias_rating"]], columns=["bias_rating"])
        df_all['bias_rating_1+2'] = df_all['bias_rating_1'] + df_all['bias_rating_2']
        value_list.append("1+2")

    elif c2 == "bias_category":
        expected_categories = {
                'generalisation',
                'prominence',
                'negative_behaviour',
                'misrepresentation',
                'headline_or_imagery'
            }
        # Find bias categories that are present in dataframe
        actual_categories = list(set(df_all.columns).intersection(expected_categories))
        df_all = df_all[['publisher']+actual_categories]
        value_list = actual_categories

    else:
        raise ValueError(f"Unknown category: {c2}")

    dict_odds = {}
    for value in value_list:
        column_name = f'{c2}_{value}' if c2 == 'bias_rating' else f'{value}'
        ct = df_all.groupby(['publisher', column_name]).size().reset_index(name='count')
        ct = ct.pivot(index='publisher', columns=column_name, values='count')
        ct = ct.reindex(index=['Others', selected_publisher], columns=[False, True])
        ct = ct.fillna(0)
        OR, pvalue = stats.fisher_exact(ct)
        dict_odds[value] = {
            'OR': OR,
            'pvalue': pvalue,
            'count': ct.iloc[1,1]
        }
    df_odds = pd.DataFrame(dict_odds).T.reset_index(names=c2)
    return df_odds

def build_bar_chart(df_corpus, publisher, c1):
    res = show_counts_c1(df_corpus, publisher, c1).set_index(c1)

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
        res['pct'] = (res['count']/res['count'].sum()).fillna(0).multiply(100).round(1)
        res = res.set_index(c1)
    else:
        res = res_top
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
    res['label'] = res['pct'].astype(int).astype(str) + '%'
    res['label'] = res['count'].astype(str) + ' (' + res['label'] + ')'

    p = (ggplot(res)
    + geom_bar(aes(x='name', y='count', fill='name'), stat='identity', width=0.60, show_legend=False)
    + geom_label(aes(x='name', y='count', label='label'), color="#474948", ha='center', size=10, show_legend=False)
    + scale_fill_manual(values=dict(zip(res['name'], res['color'])))
    + scale_y_continuous(limits=(0, res['count'].max()*1.10))
    + ylab('Number of Articles')
    + xlab(c1.replace('_', ' ').title())
    + proj_theme
    + coord_flip()
    )

    return p

def build_heatmap_chart(df_corpus, publisher, c1, c2):
    res = show_counts_c1c2(df_corpus, publisher, c1, c2)

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

    res_pct = res.div(res.sum(axis=1), axis=0).fillna(0).multiply(100)
    res.index.name = c1
    res.columns.name = c2

    # With plot labels
    res_label = res.astype(str) + '\n(' + res_pct.astype(int).astype(str) + '%)'
    res_label.columns = [x.title() + '('+y+')' for (x,y) in zip(res_label.columns.astype(str).map(c2_name_map).fillna('Others'), res.sum(axis=0).astype(int).astype(str))]
    res_label['name'] = res_label.index.astype(str).map(c1_name_map).fillna('Others')
    res_label['name_label'] = res_label['name'].astype(str) + ' (' + res.sum(axis=1).astype(int).astype(str) + ')'
    res_label['sort_index'] = res_label['name_label'].str.extract(r"\((\d+)\)", expand=False).sort_values()
    res_label = res_label.sort_values('sort_index')
    res_label = res_label.set_index('name_label').drop(columns=['name', 'sort_index'])

    # Do the same for res_pct
    res_pct['name'] = res_pct.index.astype(str).map(c1_name_map).fillna('Others')
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
    res_f[c2] = pd.Categorical(res_f[c2], categories=reversed([c for c in res_f[c2].drop_duplicates() if 'Others' in c] + [c for c in res_f[c2].drop_duplicates() if'Others' not in c]), ordered=True)

    p =(ggplot(res_f)
    + geom_tile(aes(x=c2, y=c1, fill='pct'), color='white', size=1, show_legend=False)
    + geom_label(aes(x=c2, y=c1, label='label'), color="#474948", ha='center', size=8.5, show_legend=False)
    + scale_fill_gradientn(colors=['#A8B5D3', '#03254E'], na_value='#e8e8e8')
    + xlab(c2.replace('_', ' ').title())
    + ylab(c1.replace('_', ' ').title())
    + coord_equal()
    + proj_theme
    + theme(axis_text_x = element_text(rotation=45, hjust=1))
    )

    return p

def build_odds_chart(df_corpus, selected_publisher, compared_publishers, c2):
    res = show_odds(df_corpus, selected_publisher, compared_publishers, c2).set_index(c2)

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
    + geom_label(aes(x='name_label', y='OR', label='label'), color="#474948", ha='center', size=10, show_legend=False)
    + scale_fill_manual(values=dict(zip(res['name_label'], res['color'])))
    + scale_y_continuous(limits=(0, res['OR'].max()*1.10))
    + ylab('Odds Ratio')
    + xlab(c2.replace('_', ' ').title())
    + annotate('text', x=res['name_label'].iloc[0], y=1, label='\n\n\n\n\n\n\nJust as likely', size=11, color='#4F5150')
    + annotate('text', x=res['name_label'].iloc[0], y=2, label='\n\n\n\n\n\n\nTwice as likely', size=11, color='#4F5150')
    + proj_theme
    + coord_flip()
    )

    return p
