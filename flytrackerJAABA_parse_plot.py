#toolkit to extract data from Flytracker output for JAABA
#Currently can only extract data from the JAABA trx file and any of the perframe directory files
#Can also plot tracks from the x and y data in the trx file

#importing modules
import scipy.io as spio
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import networkx as nx
import itertools


#class for extracting matlab structure type data
class struct2df():

    def __init__(self, matfile):
        """
        This class takes in a .mat structure file from the Flytracker for JAABA output and extracts the data.
        First the structure is converted to a multidimensional dictionary using the scipy.io module.
        The dictionary is parsed to ether extract specific data or extract all the data depending on the type of file.
        With trx files, queried data can be extracted or a dataframe for each fly can be exported.
        With perframe files, the parameter of the file selected is extracted into a dataframe.
        """

        #structure to dictionary
        self.mat_dict = spio.loadmat(matfile, simplify_cells=True)


        #struct2df objects
        self.trx_ls = []
        self.param_df = pd.DataFrame()
        self.scores = pd.DataFrame()
        self.processed_scores = pd.DataFrame()
        self.dtype = ''
        self.param_name = ''
        self.behavior_name = ''


        #finding the type of file that was input and loading the relevant objects
        if 'trx' in self.mat_dict.keys():
            self.dtype = 'trx'

            #df for each row of struct of trx file
            for idx in range(len(self.mat_dict['trx'])):

                seriesls = []
                for k, v in self.mat_dict['trx'][idx].items():
                    seriesls.append(pd.Series(v, name=k))

                self.trx_ls.append(pd.concat(seriesls, axis=1))




        elif 'allScores' in self.mat_dict.keys():
            self.dtype = 'scores'

            self.behavior_name = (matfile.split('/')[-1]).replace('.mat', '').replace("scores_", "")

            #making dictionaries for the perframe scores
            scores_dict = {}
            postprocessed_dict = {}

            for idx in range(len(self.mat_dict['allScores']['scores'])):
                scores_dict.update({idx+1 : self.mat_dict['allScores']['scores'][idx]})
                postprocessed_dict.update({idx+1 : self.mat_dict['allScores']['postprocessed'][idx]})

            #making dataframes for the perframe scores
            self.scores = pd.DataFrame(scores_dict)
            self.processed_scores = pd.DataFrame(postprocessed_dict)




        else:
            self.dtype = 'perframe'
            self.param_name = (matfile.split('/')[-1]).replace('.mat', '')

            #making dictionary for the perframe parameter
            new_perframe = {}
            for idx in range(len(self.mat_dict['data'])):
                new_perframe.update({idx+1 : self.mat_dict['data'][idx]})

            #making dataframe for the perframe parameter
            self.param_df = pd.DataFrame(new_perframe)
    



    #methods
    def extract_trx_param(self, param, savefile=True, name=''):
        """
        Method takes in a parameter name as a string (e.g. 'x', 'dt', etc.) or names (e.g. ['x', 'y']) as a list 
        from the trx file and loads the .param_df with a dataframe of that per frame parameter for each fly.
        If the savefile argument is True by default. If it is set to False a csv file will not be saved.
        There is an optional name argument that will add to the begining of the filename and can be used to save file to different path.
        """

        if self.dtype == 'trx':

            #formatting parameters
            paramls = []
            if isinstance(param, str):
                paramls.append(param)
            else:
                paramls = param

            #changing param name
            self.param_name = '_'.join(paramls)

            #making extracted param dataframe
            new_d = {}

            for p in paramls:
                for i in self.trx_ls:
                    l = i[p].to_list()
                    new_d.update({p + '_' + str(int((i['id'].to_list()[0]))) : l})

            self.param_df = pd.DataFrame(new_d)

            if savefile == True:
                self.param_df.to_csv('{nme}_'.format(nme=name) + '_'.join(paramls) + '.csv', index=False)

        else:
            print("Method does not support this data. Make sure data is from the trx file.")



    def save_all_trx(self, name=''):
        """
        Method to save a trx csv for each fly. the optional name argument will add to the begining of the filename and can be used to save file to different path.
        """

        if self.dtype == 'trx':

            for idx, i in enumerate(self.trx_ls):
                i.to_csv('{nme}_'.format(nme=name) + '_{fly}.csv'.format(fly=str(int(idx+1))), index=False)

        else:
            print("Method does not support this data. Make sure data is from the trx file.")



    def save_perframe_or_behavior(self, name=''):
        """
        Method saves .param_df, a dataframe of a feature perframe for each fly, to a csv file.
        There is an optional name argument that will add to the begining of the filename and can be used to save file to different path.
        """

        if self.dtype == 'perframe':
            self.param_df.to_csv('{nme}_'.format(nme=name) + self.param_name + ".csv", index=False)

        elif self.dtype == 'scores':
            self.scores.to_csv('{nme}_'.format(nme=name) + self.behavior_name + "_scores.csv", index=False)
            self.processed_scores.to_csv('{nme}_'.format(nme=name) + self.behavior_name + "_processed_scores.csv", index=False)

        else:
            print("Method does not support this data. Make sure data is from the perframe directory.")

    

    def plot_tracks(self, bysex=False, burnin=0, plottitle='', saveplot=True, filename='', showplot=False):
        """
        Method plots tracks of flies using the x,y coordinates (by pixels or mm).
        The optional argument bysex is a boolean argument that indicates whether to color the tracks by the sex of the fly
        burnin is the starting frame for which the plotting starts. it defaults to zero, the first frame.
        """

        if 'x_1' in self.param_df.columns and 'y_1' in self.param_df.columns or ('x_mm_1' in self.param_df.columns and 'y_mm_1' in self.param_df.columns):

            #getting the parameter to plot
            if 'x_1' in self.param_df.columns:
                measure = ''
            elif 'x_mm_1' in self.param_df.columns:
                measure = 'mm_'

            #setting up figure
            fig = plt.figure(figsize=(9,9))
            ax = fig.add_subplot()
            if bysex == True:

                #plotting x and y coordinates as a line plot
                for idx, i in enumerate(self.trx_ls):

                    x = self.param_df['x_{unit}{id}'.format(unit=measure, id=str(int(idx+1)))].to_list()[burnin:]
                    y = self.param_df['y_{unit}{id}'.format(unit=measure, id=str(int(idx+1)))].to_list()[burnin:]

                    if bysex == True:
                        if 'm' in i['sex'].to_list():
                            sex = 'm'
                            colr = 'blue'
                        elif 'f' in i['sex'].to_list():
                            sex = 'f'
                            colr = 'red'
                        plt.plot(x, y, label = sex, color=colr, alpha=0.7)

                #formating and showing the plot
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = dict(zip(labels, handles))
                plt.legend(by_label.values(), by_label.keys(), bbox_to_anchor=(1, 0.5), loc="center left")

            else:

                #plotting x and y coordinates as a line plot
                for idx, i in enumerate(self.trx_ls):

                    x = self.param_df['x_{unit}{id}'.format(unit=measure, id=str(int(idx+1)))].to_list()[burnin:]
                    y = self.param_df['y_{unit}{id}'.format(unit=measure, id=str(int(idx+1)))].to_list()[burnin:]

                    plt.plot(x, y, alpha=0.7)

            ax.set_aspect('equal', adjustable='box')
            plt.title(plottitle)

            if saveplot == True:
                plt.savefig('{name}{unit}x_y_tracks.png'.format(name=filename, unit=measure))
            
            if showplot == True:
                plt.show()



        else:
            print("Method does not support this data. Make sure data is from the trx file and x and y corrdinates have been extracted.")
        


    def plot_timeseries(self, fly='all', persecond=True, framerate=30, scorethreshold=None, burnin=0, plottitle='', saveplot=True, filename='', showplot=False):
        """
        Plots a line graph of a perframe feature or behavior score. Can plot lines for all flies or select flies.
        If the type of data is JAABA behavior data, the method outputs a scores and processed scores plots.
        persecond argment defaults to true to plot data averaged per second. Set to False to plot per frame.
        framerate defaults to 30 fps. Check the framerate of your experiement and change accordingly.
        The fly argument defaults to all, but this can be changed to a fly id or a list of fly ids.
        plottitle and filename are optional arguments. filename adds to the beginning of the filename, there is a default name for the file.
        Optional arguments to save the plot and show the plot.
        scorethreshold defaults to None, but change to a float to set a lower limit to the processed behavior score
        burnin is the starting frame at which the plotting should start. If the plotting is set to seconds the method converts the frame to seconds.
        """

        #formatting fly parameter
        flyls = []
        if not isinstance(fly, list) and fly != 'all':
            flyls.append(fly)
        else:
            flyls = fly

        
        #setting burnin
        if persecond == True:
            bi = int(burnin / framerate)
        else:
            bi = burnin

        
        #getting unit
        if persecond == True:
            unit = "Seconds"
        else:
            unit = "Frames"


        if self.dtype == 'perframe':
            plt.figure(figsize=(15,5))

            if fly == 'all':
                #plotting x and y coordinates as a line plot
                for idx, i in enumerate(self.mat_dict['data']):
                    if persecond == True:
                        modi = np.append(i, [0 for j in range((framerate - (len(i) % framerate)))])
                        ls = np.average(modi.reshape(-1, framerate), axis=1)
                    else:
                        ls = i
                    plt.plot(ls, label=idx+1)

                #formating and showing the plot
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = dict(zip(labels, handles))
                plt.legend(by_label.values(), by_label.keys(), loc='center left', bbox_to_anchor=(1, 0.5))

            elif len(flyls) == 1:
                for i in flyls:
                    if persecond == True:
                        modls = np.append(self.mat_dict['data'][int(i)-1], [0 for j in range((framerate - (len(self.mat_dict['data'][int(i)-1]) % framerate)))])
                        ls = np.average(modls.reshape(-1, framerate), axis=1)
                    else:
                        ls = self.mat_dict['data'][int(i)-1]
                    plt.plot(ls)

            else:
                for i in flyls:
                    if persecond == True:
                        modls = np.append(self.mat_dict['data'][int(i)-1], [0 for j in range((framerate - (len(self.mat_dict['data'][int(i)-1]) % framerate)))])
                        ls = np.average(modls.reshape(-1, framerate), axis=1)
                    else:
                        ls = self.mat_dict['data'][int(i)-1]
                    plt.plot(ls)

                #formating and showing the plot
                handles, labels = plt.gca().get_legend_handles_labels()
                by_label = dict(zip(labels, handles))
                plt.legend(by_label.values(), by_label.keys(), loc='center left', bbox_to_anchor=(1, 0.5))

            plt.xlim(left=bi, right=len(ls))
            plt.xlabel(unit)
            plt.ylabel(self.param_name)
            plt.title(plottitle)

            if saveplot == True:
                plt.savefig('{name}{default}_perframe_plot.png'.format(name=filename, default=self.param_name))
            
            if showplot == True:
                plt.show()

        



        elif self.dtype == 'scores':
            for thing2plot in ['scores', 'postprocessed']:
                plt.figure(figsize=(15,5))

                if fly == 'all':
                    #plotting x and y coordinates as a line plot
                    for idx, i in enumerate(self.mat_dict['allScores'][thing2plot]):
                        if persecond == True:
                            modi = np.append(i, [0 for j in range((framerate - (len(i) % framerate)))])
                            ls = np.average(modi.reshape(-1, framerate), axis=1)
                        else:
                            ls = i
                        plt.plot(ls, label=idx+1, alpha=0.5)
                        if thing2plot == 'postprocessed':
                            plt.fill_between([j for j in range(len(ls))], ls, alpha=0.5)
                            if scorethreshold != None:
                                plt.ylim(bottom=scorethreshold, top=1)
                            else:
                                plt.ylim(top=1)

                    #formating and showing the plot
                    handles, labels = plt.gca().get_legend_handles_labels()
                    by_label = dict(zip(labels, handles))
                    leg = plt.legend(by_label.values(), by_label.keys(), loc='center left', bbox_to_anchor=(1, 0.5))
                    for obj in leg.get_lines():
                        obj.set_linewidth(5)

                elif len(flyls) == 1:
                    for i in flyls:
                        if persecond == True:
                            modls = np.append(self.mat_dict['allScores'][thing2plot][int(i)-1], [0 for j in range((framerate - (len(self.mat_dict['allScores'][thing2plot][int(i)-1]) % framerate)))])
                            ls = np.average(modls.reshape(-1, framerate), axis=1)
                        else:
                            ls = self.mat_dict['allScores'][thing2plot][int(i)-1]
                        plt.plot(ls)

                        if thing2plot == 'postprocessed':
                            plt.fill_between([i for i in range(len(ls))], ls)
                            if scorethreshold != None:
                                plt.ylim(bottom=scorethreshold, top=1)
                            else:
                                plt.ylim(top=1)
                                
                        

                else:
                    for i in flyls:
                        if persecond == True:
                            modls = np.append(self.mat_dict['allScores'][thing2plot][int(i)-1], [0 for j in range((framerate - (len(self.mat_dict['allScores'][thing2plot][int(i)-1]) % framerate)))])
                            ls = np.average(modls.reshape(-1, framerate), axis=1)
                        else:
                            ls = self.mat_dict['allScores'][thing2plot][int(i)-1]
                        plt.plot(ls, label=i, alpha=0.5)
                        if thing2plot == 'postprocessed':
                            plt.fill_between([i for i in range(len(ls))], ls, alpha=0.5)
                            if scorethreshold != None:
                                plt.ylim(bottom=scorethreshold, top=1)
                            else:
                                plt.ylim(top=1)

                    #formating and showing the plot
                    handles, labels = plt.gca().get_legend_handles_labels()
                    by_label = dict(zip(labels, handles))
                    leg = plt.legend(by_label.values(), by_label.keys(), loc='center left', bbox_to_anchor=(1, 0.5))
                    for obj in leg.get_lines():
                        obj.set_linewidth(5)

                #scores or postprocessed
                if thing2plot == 'scores':
                    ylabelname = ' score'
                else:
                    ylabelname = ' processed score'

                plt.xlim(left=bi, right=len(ls))
                plt.xlabel(unit)
                plt.ylabel(self.behavior_name + ylabelname)
                plt.title(plottitle)

                if saveplot == True:
                    plt.savefig('{name}{default}_{flies}_{thing}_plot.png'.format(name=filename, default=self.param_name, flies=str(fly), thing=thing2plot))
                
                if showplot == True:
                    plt.show()





#class for organizing a fly experiment using struct2df instances
class fly_experiment():

    def __init__(self, structdfls):
        """
        Note that this class cannot be imported without also importing struct2df.
        This class takes in a list of instances of struct2df from the same fly experiment.
        The instantiation of the class needs the trx.mat file and any other .mat file you want to include.
        This class will load data into multiple lists and dictionaries which can be referenced and are referenced by methods.
        The ethogram method needs processed behavior score mat files.
        The network method needs the dcenter parameter and an optional behavior processed score file.
        """

        #objects that can be referenced
        self.trx_ls = []
        self.trxs = {}
        self.perframes = {} #also includes any extracted parameters from trx
        self.jaaba_scores = {}
        self.jaaba_processed = {}
        self.sex = {}

        #loading data into objects
        for i in structdfls:

            if i.dtype == 'trx':
                self.trx_ls = i.trx_ls

                for idx, j in enumerate(i.trx_ls):
                    self.trxs.update({idx+1: j})
                    self.sex.update({idx+1: j['sex'].to_list()[0]})

                if i.param_df.empty:
                    continue
                else:
                    self.perframes.update({'trx_' + i.param_name: i.param_df})
                

            elif i.dtype == 'perframe':
                self.perframes.update({i.param_name: i.param_df})


            else:
                self.jaaba_scores.update({i.behavior_name: i.scores})
                self.jaaba_processed.update({i.behavior_name: i.processed_scores})

    

    #methods
    def stack_timeseries(self, params="all", behavior_scores="all", behavior_processed="all", savefile=False, name=''):
        """
        The default behavior of this method is to put every perframe feature including behavior scores into one dataframe that is returned.
        The params, behavior_scores, and behavior_processed arguments can be set to the name of one or a few (str or list) features instead of all features.
        If the savefile argument is False by default. If it is set to True a csv file will be saved.
        There is an optional name argument that will add to the begining of the filename and can be used to save file to different path.
        """

        #getting lists of features to extract
        paramls = []
        scoresls = []
        processedls = []

        if not isinstance(params, list) and params != 'all':
            paramls.append(params)
        elif params == 'all':
            paramls = list(self.perframes.keys())
        else:
            paramls = params

        
        if not isinstance(behavior_scores, list) and behavior_scores != 'all':
            scoresls.append(behavior_scores)
        elif behavior_scores == 'all':
            scoresls = list(self.jaaba_scores.keys())
        else:
            scoresls = behavior_scores


        if not isinstance(behavior_processed, list) and behavior_processed != 'all':
            processedls.append(behavior_processed)
        elif behavior_processed == 'all':
            processedls = list(self.jaaba_processed.keys())
        else:
            processedls = behavior_processed

        
        #stacking data
        stackdf = pd.DataFrame()

        for i in paramls:
            df = self.perframes[i]

            if 'trx' not in i:
                df = df.add_prefix(i + '_')

            if stackdf.empty:
                stackdf = df
            else:
                stackdf = pd.merge(stackdf, df, left_index=True, right_index=True)

        
        for i in scoresls:
            df = self.jaaba_scores[i]
            df = df.add_prefix(i + '_score_')

            if stackdf.empty:
                stackdf = df
            else:
                stackdf = pd.merge(stackdf, df, left_index=True, right_index=True)


        for i in processedls:
            df = self.jaaba_processed[i]
            df = df.add_prefix(i + '_processed_')

            if stackdf.empty:
                stackdf = df
            else:
                stackdf = pd.merge(stackdf, df, left_index=True, right_index=True)


        #saving df
        if savefile == True:
            superlist = paramls + scoresls + processedls
            stackdf.to_csv('{nme}_'.format(nme=name) + '_'.join(superlist) + '.csv', index=False)

        return stackdf

        

    def ethogram(self, burnin=0, scorethreshold=None, fly="all", framerate=30, plottitle="", showplot=False, saveplot=True, filename=""):
        """
        Method to plot a pseudo-ethogram of all loaded behaviors for all flies, subset of flies, or single fly.
        The burnin can be set to the SECOND to start the plot at. Note that this is different from the struct2df method which takes the frame to start at.
        The average behavior score threshold can also be set, but defaults to zero.
        The flies defaults to a plot of all flies but can be set to a subset of flies which is input as a list of flies or a single fly id.
        'm' or 'f' can also be passed to select just male or female flies.
        """

        #selecting flies
        flyls = []

        if fly == 'all':
            for idx in range(len(self.trx_ls)):
                flyls.append(idx+1)
            opacity = 0.5

        elif isinstance(fly, list):
            flyls = fly
            opacity = 0.5

        elif fly == 'm':
            for i in self.sex.keys():
                if self.sex[i] == 'm':
                    flyls.append(i)
            flyls.sort()
            opacity = 0.5

        elif fly == 'f':
            for i in self.sex.keys():
                if self.sex[i] == 'f':
                    flyls.append(i)
            flyls.sort()
            opacity = 0.5

        else:
            flyls.append(fly)
            opacity = 1


        #getting behaviors
        behaviors = list(self.jaaba_processed.keys())

        #plotting
        fig, ax = plt.subplots(len(behaviors), 1, sharex='col', figsize=(20,7))
        for i in range(len(behaviors)):

            #averaging dataframe per second
            framesdf = self.jaaba_processed[behaviors[i]]
            persec = framesdf.groupby(np.arange(len(framesdf))//framerate).mean()

            for id in flyls:

                ax[i].plot(persec[id].to_list(), label=id, alpha=opacity)
                ax[i].fill_between([i for i in range(len(persec[id].to_list()))], persec[id].to_list(), alpha=opacity)
                ax[i].set_ylabel(behaviors[i])

                if scorethreshold != None:
                    ax[i].set_ylim(bottom=scorethreshold, top=1)
                else:
                    ax[i].set_ylim(top=1)

        plt.xlim(left=burnin, right=len(persec[id].to_list()))
        plt.xlabel("seconds")
        plt.suptitle(plottitle)

        #formating and showing the plot
        if len(flyls) != 1:
            handles, labels = plt.gca().get_legend_handles_labels()
            by_label = dict(zip(labels, handles))
            leg = plt.legend(by_label.values(), by_label.keys(), loc='lower center', bbox_to_anchor=(0.5, -0.32), ncol=len(flyls))
            for obj in leg.get_lines():
                obj.set_linewidth(5)

        if showplot == True:
            plt.show()

        if saveplot == True:
            plt.savefig('{name}_ethogram_{flies}.png'.format(name=filename, flies=str(fly)))


                
    def network(self, dist_threshold=2, behavior=None, behavior_threshold=0.5, burnin=0, framerate=30, plottitle="", showplot=False, saveplot=True, filename=""):
        """
        Method using the dcenter parameter to find interactions between flies.
        Interactions can be coupled to a chosen behavior for a more acurate fly-to-fly behavioral network.
        The distance threshold is the distance between two flies that counts as an interaction.
        Burnin can be set to the starting SECOND not frame.
        Framrate defaults to 30. Check the framrate of your experiment.
        """

        #getting pairs
        colnames = list(self.perframes['dcenter'].columns)
        colnames = ['dcenter_' + str(i) for i in colnames]

        pairs = list(itertools.combinations(colnames, 2))
        connections = {}
        for i in pairs:
            connections.update({i:0})

        
        #stacking timeseries of dcenter and behavior
        if behavior == None:
            stack = self.perframes['dcenter']
            stack = stack.add_prefix('dcenter_')

        else:
            stack = self.stack_timeseries(params='dcenter', behavior_scores=[], behavior_processed=behavior)

        #making stack per second
        stack = stack.groupby(np.arange(len(stack))//framerate).mean()
        stack = stack[burnin:]

        #selecting for behavior, dropping behavior columns
        if behavior != None:
            behavior_df = stack.filter(like=behavior, axis=1)
            stack['boolean'] = behavior_df.apply(lambda row: any(val >= behavior_threshold for val in row.values), axis=1)

            stack = stack.drop(stack[stack.boolean == False].index)

            stack = stack.loc[:, stack.columns.str.contains('dcenter_')]

        #finding interactions
        cols_below_threshold = lambda row: list(stack.columns[row <= dist_threshold])
        stack['interactions'] = stack.apply(cols_below_threshold, axis=1)
        
        stack = stack[stack['interactions'].map(lambda d: len(d)) > 1]
        

        #getting weights based on frequency of interactions (pairwise)
        for i in stack['interactions'].to_list():
            row_tuples = list(itertools.combinations(i, 2))

            for j in row_tuples:
                connections[j] += 1
        
        #making network df
        nw_df = pd.DataFrame.from_dict(connections, orient='index', columns=['weight'])
        nw_df = nw_df.reset_index().rename(columns={'index': 'tuples'})

        #nw_df = nw_df.drop(nw_df[nw_df['weight'] == 0].index)

        nw_df[['node1', 'node2']] = nw_df['tuples'].apply(lambda x: pd.Series([x[0], x[1]]))
        nw_df = nw_df.drop('tuples', axis=1)
        nw_df = nw_df.replace(to_replace='dcenter_', value='', regex=True)
        nw_df = nw_df.loc[:,['node1','node2','weight']]


        #formatting plot
        plt.figure(figsize=(8,8))
        ax = plt.gca()
        ax.set_title(plottitle)


        ###making network
        # create an empty undirected graph
        G = nx.Graph()

        #node colors
        colors = {}
        for k in self.sex.keys():
            if self.sex[k] == 'm':
                colors.update({k:'blue'})
            else:
                colors.update({k:'red'})

        # add nodes with their respective colors, ordering nodes by fly id
        nodes = list(set(nw_df['node1']).union(set(nw_df['node2'])))
        nodes = [int(i) for i in nodes]
        nodes.sort()
        nodes = [str(i) for i in nodes]

        for node in nodes:
            col = colors.get(node, 'gray') # use the color from the dictionary, or default to gray
            G.add_node(node, color=col)
        

        # add edges with their respective weights
        for index, row in nw_df.iterrows():
            G.add_edge(row['node1'], row['node2'], weight=row['weight'])

        # draw the graph
        pos = nx.circular_layout(G)
        weights = [G[u][v]['weight'] for u, v in G.edges()]
        nx.draw(G, pos, width=((weights/nw_df['weight'].max()) * 15), edge_color='gray', node_color=[colors[int(node)] for node in G.nodes()])
        nx.draw_networkx_labels(G, pos, font_size=12, font_color='white')


        if showplot == True:
            plt.show()

        if saveplot == True:
            plt.savefig('{name}_{d}mm_behavior_{b}_network.png'.format(name=filename, d=str(dist_threshold), b=behavior))




