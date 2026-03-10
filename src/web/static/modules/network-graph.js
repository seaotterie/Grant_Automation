/**
 * Network Graph — Six Degrees Connection Visualizer
 *
 * Renders a D3.js force-directed network graph showing:
 *   - Profile org (center, blue)
 *   - Profile people (teal, inner ring left)
 *   - Funder orgs (colored by connection strength, right)
 *   - Funder people (amber, outer ring right)
 *   - Connection edges: membership (thin gray), direct match (green),
 *                        shared background (amber dashed), opportunity link (blue)
 *
 * Entry point: window.renderNetworkGraph(svgEl, profileName, pipelineResult)
 */

(function () {
    'use strict';

    /**
     * Build D3-compatible nodes/links arrays from pipelineResult data.
     */
    function buildGraphData(profileName, pipelineResult) {
        const nodes = [];
        const links = [];
        const nodeIndex = {};   // id → index (populated after nodes array is built)

        function addNode(node) {
            nodes.push(node);
        }

        // ── Profile org ───────────────────────────────────────────────────
        addNode({ id: 'profile', type: 'org', label: profileName || 'Your Org', group: 0 });

        // ── Profile people ────────────────────────────────────────────────
        for (const p of (pipelineResult.profile_people || [])) {
            const id = 'pp_' + p.name;
            addNode({ id, type: 'profile_person', label: p.name, title: p.title || '', source: p.source || '', group: 1 });
            links.push({ source: 'profile', target: id, type: 'member', strength: 0.4 });
        }

        // ── Funder orgs + their people + connection edges ─────────────────
        for (const conn of (pipelineResult.network_connections || [])) {
            const funderId = 'funder_' + (conn.funder_ein || conn.funder_name);
            const strengthColor = {
                strong:   '#16a34a',
                moderate: '#d97706',
                weak:     '#6b7280',
                none:     '#9ca3af',
                unknown:  '#3b82f6',
            }[conn.connection_strength] || '#6b7280';

            addNode({
                id: funderId,
                type: 'funder',
                label: conn.funder_name,
                strength: conn.connection_strength || 'unknown',
                score: conn.screening_score || 0,
                color: strengthColor,
                group: 2,
            });

            // Opportunity link (profile → funder)
            links.push({
                source: 'profile',
                target: funderId,
                type: 'opportunity',
                strength: 0.15,
                score: conn.screening_score || 0,
            });

            // Funder people
            for (const fp of (conn.funder_people || [])) {
                const fpId = 'fp_' + (conn.funder_ein || conn.funder_name) + '_' + fp.name;
                if (!nodes.find(n => n.id === fpId)) {
                    addNode({ id: fpId, type: 'funder_person', label: fp.name, title: fp.title || '', source: fp.source || '', group: 3 });
                }
                links.push({ source: funderId, target: fpId, type: 'member', strength: 0.4 });
            }

            // Direct match edges (profile person ↔ funder person)
            for (const m of (conn.direct_matches || [])) {
                const spId = 'pp_' + m.seeker_person;
                const fpId = 'fp_' + (conn.funder_ein || conn.funder_name) + '_' + m.funder_person;
                if (nodes.find(n => n.id === spId) && nodes.find(n => n.id === fpId)) {
                    links.push({ source: spId, target: fpId, type: 'direct', basis: m.basis || '', strength: 1.0 });
                }
            }

            // Shared background edges (first seeker ↔ first funder person)
            for (const bg of (conn.shared_background || [])) {
                const seekers = bg.seeker_people || [];
                const funders = bg.funder_people || [];
                if (seekers.length && funders.length) {
                    const spId = 'pp_' + seekers[0];
                    const fpId = 'fp_' + (conn.funder_ein || conn.funder_name) + '_' + funders[0];
                    if (nodes.find(n => n.id === spId) && nodes.find(n => n.id === fpId)) {
                        links.push({ source: spId, target: fpId, type: 'shared', basis: bg.basis || '', strength: 0.7 });
                    }
                }
            }
        }

        return { nodes, links };
    }

    /**
     * Render the network graph into the given SVG element.
     * @param {SVGElement} svgEl   - target SVG element (will be cleared and redrawn)
     * @param {string}     profileName
     * @param {object}     pipelineResult - from Alpine.js pipelineResult
     */
    window.renderNetworkGraph = function (svgEl, profileName, pipelineResult) {
        if (!svgEl || !pipelineResult) return;
        if (typeof d3 === 'undefined') {
            console.warn('[NetworkGraph] D3.js not loaded');
            return;
        }

        const { nodes, links } = buildGraphData(profileName, pipelineResult);
        if (nodes.length === 0) return;

        // ── Setup ──────────────────────────────────────────────────────────
        const svg = d3.select(svgEl);
        svg.selectAll('*').remove();

        const rect = svgEl.getBoundingClientRect();
        const W = rect.width  || 800;
        const H = rect.height || 600;

        svg.attr('width', W).attr('height', H);

        // Zoom layer
        const g = svg.append('g').attr('class', 'graph-root');
        svg.call(d3.zoom()
            .scaleExtent([0.2, 4])
            .on('zoom', (event) => g.attr('transform', event.transform))
        );

        // ── Color helpers ─────────────────────────────────────────────────
        const NODE_COLOR = {
            org:            '#3b82f6',  // blue — profile org
            profile_person: '#0d9488',  // teal — seeker people
            funder:         null,       // set per-node from conn.color
            funder_person:  '#f59e0b',  // amber — funder people
        };
        const LINK_COLOR = {
            member:      '#d1d5db',
            opportunity: '#93c5fd',
            direct:      '#16a34a',
            shared:      '#d97706',
        };
        const NODE_RADIUS = {
            org:            22,
            profile_person: 13,
            funder:         17,
            funder_person:  10,
        };

        // ── Force simulation ──────────────────────────────────────────────
        const simulation = d3.forceSimulation(nodes)
            .force('link', d3.forceLink(links)
                .id(d => d.id)
                .distance(d => {
                    if (d.type === 'opportunity') return 180;
                    if (d.type === 'direct')      return 80;
                    if (d.type === 'shared')       return 100;
                    return 70; // member
                })
                .strength(d => d.strength || 0.3)
            )
            .force('charge', d3.forceManyBody().strength(-200))
            .force('center', d3.forceCenter(W / 2, H / 2))
            .force('collision', d3.forceCollide().radius(d => (NODE_RADIUS[d.type] || 12) + 6))
            .force('x', d3.forceX(d => {
                // Bias positions: profile org center, profile people left, funders right
                if (d.type === 'org')            return W * 0.5;
                if (d.type === 'profile_person') return W * 0.25;
                if (d.type === 'funder')         return W * 0.70;
                if (d.type === 'funder_person')  return W * 0.85;
                return W * 0.5;
            }).strength(0.12))
            .force('y', d3.forceY(H / 2).strength(0.04));

        // ── Arrow markers ─────────────────────────────────────────────────
        const defs = svg.append('defs');
        ['member', 'opportunity', 'direct', 'shared'].forEach(type => {
            defs.append('marker')
                .attr('id', 'arrow-' + type)
                .attr('viewBox', '0 -5 10 10')
                .attr('refX', 20)
                .attr('refY', 0)
                .attr('markerWidth', 6)
                .attr('markerHeight', 6)
                .attr('orient', 'auto')
                .append('path')
                .attr('d', 'M0,-5L10,0L0,5')
                .attr('fill', LINK_COLOR[type] || '#ccc');
        });

        // ── Links ─────────────────────────────────────────────────────────
        const link = g.append('g').attr('class', 'links')
            .selectAll('line')
            .data(links)
            .join('line')
            .attr('stroke', d => LINK_COLOR[d.type] || '#ccc')
            .attr('stroke-width', d => d.type === 'direct' ? 2.5 : d.type === 'shared' ? 2 : 1)
            .attr('stroke-dasharray', d => d.type === 'shared' ? '5,3' : null)
            .attr('stroke-opacity', d => d.type === 'opportunity' ? 0.35 : 0.7)
            .attr('marker-end', d => `url(#arrow-${d.type})`);

        // ── Tooltip ───────────────────────────────────────────────────────
        const tooltip = d3.select('body').selectAll('.ng-tooltip').data([null]).join('div')
            .attr('class', 'ng-tooltip')
            .style('position', 'fixed')
            .style('pointer-events', 'none')
            .style('background', 'rgba(15,23,42,0.9)')
            .style('color', '#f1f5f9')
            .style('padding', '6px 10px')
            .style('border-radius', '6px')
            .style('font-size', '12px')
            .style('max-width', '240px')
            .style('z-index', '9999')
            .style('display', 'none');

        // ── Nodes ─────────────────────────────────────────────────────────
        const node = g.append('g').attr('class', 'nodes')
            .selectAll('g')
            .data(nodes)
            .join('g')
            .attr('class', 'node')
            .style('cursor', 'pointer')
            .call(d3.drag()
                .on('start', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x; d.fy = d.y;
                })
                .on('drag', (event, d) => { d.fx = event.x; d.fy = event.y; })
                .on('end', (event, d) => {
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null; d.fy = null;
                })
            )
            .on('mouseover', (event, d) => {
                let html = `<strong>${d.label}</strong>`;
                if (d.title) html += `<br><span style="opacity:0.75">${d.title}</span>`;
                if (d.type === 'funder') html += `<br>Strength: <em>${d.strength}</em>`;
                if (d.type === 'funder' && d.score) html += ` · Score: ${Math.round(d.score * 100)}%`;
                if (d.source) html += `<br><span style="opacity:0.6">Source: ${d.source}</span>`;
                tooltip.style('display', 'block').html(html);
            })
            .on('mousemove', (event) => {
                tooltip.style('left', (event.clientX + 14) + 'px').style('top', (event.clientY - 10) + 'px');
            })
            .on('mouseout', () => tooltip.style('display', 'none'));

        // Circle
        node.append('circle')
            .attr('r', d => NODE_RADIUS[d.type] || 12)
            .attr('fill', d => d.color || NODE_COLOR[d.type] || '#6b7280')
            .attr('stroke', '#fff')
            .attr('stroke-width', d => d.type === 'org' ? 3 : 1.5);

        // Label (show for org + funder nodes; truncated for people)
        node.append('text')
            .attr('dy', d => (NODE_RADIUS[d.type] || 12) + 12)
            .attr('text-anchor', 'middle')
            .attr('font-size', d => d.type === 'org' || d.type === 'funder' ? '11px' : '9px')
            .attr('fill', '#374151')
            .attr('class', 'dark:fill-gray-200')
            .text(d => {
                const maxLen = d.type === 'org' || d.type === 'funder' ? 20 : 14;
                return d.label.length > maxLen ? d.label.slice(0, maxLen - 1) + '…' : d.label;
            });

        // ── Legend ────────────────────────────────────────────────────────
        const legendData = [
            { color: '#3b82f6', label: 'Your Org' },
            { color: '#0d9488', label: 'Your People' },
            { color: '#16a34a', label: 'Funder (strong)' },
            { color: '#d97706', label: 'Funder (moderate)' },
            { color: '#f59e0b', label: 'Funder People' },
        ];
        const legend = svg.append('g').attr('transform', 'translate(16, 16)');
        legendData.forEach((item, i) => {
            const row = legend.append('g').attr('transform', `translate(0, ${i * 20})`);
            row.append('circle').attr('r', 6).attr('cx', 6).attr('cy', 0).attr('fill', item.color);
            row.append('text').attr('x', 16).attr('dy', '0.35em').attr('font-size', '11px')
               .attr('fill', '#6b7280').text(item.label);
        });

        // Edge legend
        const edgeLegendData = [
            { color: '#16a34a', dash: null,  label: 'Direct match' },
            { color: '#d97706', dash: '5,3', label: 'Shared background' },
            { color: '#93c5fd', dash: null,  label: 'Opportunity link' },
        ];
        const edgeLegend = svg.append('g').attr('transform', `translate(16, ${16 + legendData.length * 20 + 12})`);
        edgeLegendData.forEach((item, i) => {
            const row = edgeLegend.append('g').attr('transform', `translate(0, ${i * 18})`);
            row.append('line').attr('x1', 0).attr('y1', 0).attr('x2', 18).attr('y2', 0)
               .attr('stroke', item.color).attr('stroke-width', 2)
               .attr('stroke-dasharray', item.dash);
            row.append('text').attr('x', 24).attr('dy', '0.35em').attr('font-size', '11px')
               .attr('fill', '#6b7280').text(item.label);
        });

        // ── Tick ─────────────────────────────────────────────────────────
        simulation.on('tick', () => {
            link
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
            node.attr('transform', d => `translate(${d.x},${d.y})`);
        });

        // Run for a bit then slow down
        simulation.alpha(1).restart();
        setTimeout(() => simulation.alphaTarget(0), 3000);
    };

})();
