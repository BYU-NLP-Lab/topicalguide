/**
 * The Topic Browser
 * Copyright 2010-2011 Brigham Young University
 * 
 * This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
 * 
 * The Topic Browser is free software: you can redistribute it and/or modify it
 * under the terms of the GNU Affero General Public License as published by the
 * Free Software Foundation, either version 3 of the License, or (at your
 * option) any later version.
 * 
 * The Topic Browser is distributed in the hope that it will be useful, but
 * WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
 * FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
 * for more details.
 * 
 * You should have received a copy of the GNU Affero General Public License
 * along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * If you have inquiries regarding any further use of the Topic Browser, please
 * contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
 * Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.
 */
package edu.byu.nlp.topicvis;

import java.util.HashSet;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import javax.swing.Icon;
import javax.swing.JPanel;

import org.gephi.filters.api.FilterLibrary;
import org.gephi.filters.plugin.graph.DegreeRangeBuilder;
import org.gephi.filters.spi.Category;
import org.gephi.filters.spi.ComplexFilter;
import org.gephi.filters.spi.Filter;
import org.gephi.filters.spi.FilterBuilder;
import org.gephi.filters.spi.FilterProperty;
import org.gephi.graph.api.Graph;
import org.gephi.graph.api.Node;
import org.openide.util.NbBundle;
import org.openide.util.lookup.ServiceProvider;

@ServiceProvider(service = FilterBuilder.class)
public class NeighborFilterBuilder implements FilterBuilder {

	public Category getCategory() {
		return FilterLibrary.TOPOLOGY;
	}

	public String getName() {
		return NbBundle.getMessage(DegreeRangeBuilder.class, "NeighborFilterBuilder.name");
	}

	public Icon getIcon() {
		return null;
	}

	public String getDescription() {
		return null;
	}

	public Filter getFilter() {
		return new NeighborFilter();
	}

	public JPanel getPanel(Filter filter) {
		return null;
	}

	public static class NeighborFilter implements ComplexFilter {
		private String nodeIDregex = "";

		@Override
		public String getName() {
			return this.getClass().getName();
		}

		@Override
		public FilterProperty[] getProperties() {
			try {
				return new FilterProperty[]{
						FilterProperty.createProperty(this, String.class, "pattern")};
			} catch (NoSuchMethodException ex) {
				ex.printStackTrace();
			}
			return new FilterProperty[0];
		}

		@Override
		public Graph filter(Graph graph) {
			final Set<Node> matchers = matchingNodes(graph);
			final Set<Node> result = new HashSet<Node>();
			for(final Node matcher : matchers) {
				result.add(matcher);
				for(Node neighbor : graph.getNeighbors(matcher)) {
					result.add(neighbor);
				}
			}
			for (Node node : graph.getNodes().toArray()) {
				if (!result.contains(node)) {
					graph.removeNode(node);
				}
			}
			return graph;
		}

		private Set<Node> matchingNodes(final Graph graph) {
			final Pattern regex = Pattern.compile(nodeIDregex);
			final Set<Node> nodes = new HashSet<Node>();
			for (Node n : graph.getNodes()) {
				final Matcher m = regex.matcher(n.getNodeData().getId());
				if(m.find())
					nodes.add(n);
			}
			return nodes;
		}

		public String getPattern() {
			return nodeIDregex;
		}

		public void setPattern(String nodeIDregex) {
			this.nodeIDregex = nodeIDregex;
		}
	}//end class NeighborFilter
}