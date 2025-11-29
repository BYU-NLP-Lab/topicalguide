

class AbstractTopicNamer(object):
    """
    TopicNamers must have:
    Required Property:
    name_scheme -- the name of the scheme
    
    Required Function:
    name_topics -- takes an Analysis Django database object and saves to the 
                   database the topic to scheme_name assignments
    """
    def __init__(self):
        self.name_scheme = None
    
    def name_topics(self, analysis_db):
        """Name the topics in the analysis and save them to the database.
        analysis_db -- an Analysis Django object
        """
        raise NotImplementedError('name_topics is not implemented')
