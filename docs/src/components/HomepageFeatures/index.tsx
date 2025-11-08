import type {ReactNode} from 'react';
import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

type FeatureItem = {
  title: string;
  Svg: React.ComponentType<React.ComponentProps<'svg'>>;
  description: ReactNode;
};

const FeatureList: FeatureItem[] = [
  {
    title: 'Statistical Semantic Discovery',
    Svg: require('@site/static/img/undraw_docusaurus_mountain.svg').default,
    description: (
      <>
        Automatically discovers semantic relationships by analyzing value 
        co-occurrence patterns across table corpora. Handles entity variations, 
        hierarchical relationships, and code mappings without manual rules.
      </>
    ),
  },
  {
    title: 'PMI-Based Join Quality',
    Svg: require('@site/static/img/undraw_docusaurus_tree.svg').default,
    description: (
      <>
        Uses Pointwise Mutual Information scores to quantify relationship strength. 
        Two proven algorithms: CS-JP-LP for optimal quality and RS-JP for efficient 
        performance with quality superior to traditional approaches.
      </>
    ),
  },
  {
    title: 'Corpus-Driven Intelligence',
    Svg: require('@site/static/img/undraw_docusaurus_react.svg').default,
    description: (
      <>
        Based on Microsoft Research paper. Pre-computes semantic relationships 
        from your table corpus, enabling fast joins that understand your data 
        domain without external knowledge bases.
      </>
    ),
  },
];

function Feature({title, Svg, description}: FeatureItem) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <Svg className={styles.featureSvg} role="img" />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures(): ReactNode {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
